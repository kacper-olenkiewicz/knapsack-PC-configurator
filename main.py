import pandas as pd
import random
from utils import load_data, get_components_by_category, filter_by_max_price, remove_nan_categories

class PCBuilder:
    def __init__(self, budget: float, mode: str, data_path: str = 'dataset.csv'):
        self.budget = budget
        self.mode = mode
        self.data_path = data_path
        
        self.df = pd.DataFrame()
        self.categories = []
        self.ordered_categories = []
        self.base_min_prices = {}

    def initialize(self) -> bool:
        self.df = load_data(self.data_path)
        if self.df.empty:
            return False
            
        cols_to_numeric = ['Price_PLN', 'Performance_Score', 'TDP_W', 'Power_W', 'Length_mm', 'Height_mm']
        for col in cols_to_numeric:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
        self.df = remove_nan_categories(self.df, column='Category')
        self.categories = list(self.df['Category'].unique())
        
        for cat in self.categories:
            self.base_min_prices[cat] = self.df[self.df['Category'] == cat]['Price_PLN'].min()
            
        priority_order = ['GPU', 'CPU', 'Motherboard', 'RAM', 'Storage', 'Power Supply', 'Case', 'CPU Cooler']
        for c in self.categories:
            if c not in priority_order: priority_order.append(c)
        self.ordered_categories = [c for c in priority_order if c in self.categories]
        
        return True

    def build(self, num_candidates: int = 200):
        if not self.initialize():
            return None

        valid_builds = []
        
        for attempt in range(num_candidates):
            mutated_weights = self._generate_mutated_weights()
            success, components, spent, remaining, tdp, build_log = self._attempt_single_build(mutated_weights)
            
            if success:
                score = self._evaluate_fitness(components, spent)
                valid_builds.append({
                    'score': score,
                    'components': components,
                    'spent': spent,
                    'remaining': remaining,
                    'tdp': tdp,
                    'log': build_log
                })
        
        if not valid_builds:
            return None
            
        valid_builds.sort(key=lambda x: x['score'], reverse=True)
        return valid_builds[0]

    def _generate_mutated_weights(self):
        if self.mode == '2':
            base = {'CPU': 0.35, 'RAM': 0.20, 'Motherboard': 0.15, 'Storage': 0.10, 'GPU': 0.15, 'Power Supply': 0.05}
        else:
            base = {'GPU': 0.45, 'CPU': 0.20, 'Motherboard': 0.10, 'RAM': 0.08, 'Storage': 0.07, 'Power Supply': 0.05, 'Case': 0.05}
            
        mutated = {}
        for k, v in base.items():
            mutated[k] = v * random.uniform(0.75, 1.25) 
        
        total = sum(mutated.values())
        return {k: v/total for k, v in mutated.items()}

    def _evaluate_fitness(self, components, total_spent):
        total_perf = sum(c['Performance_Score'] for c in components)
        score = total_perf - (total_spent * 0.005) 
        return round(score, 2)

    def _attempt_single_build(self, weights):
        components = []
        total_spent = 0
        remaining_budget = self.budget
        chosen_socket, chosen_ram_type = None, None
        total_tdp = 0
        gpu_score, cpu_score = 0, 0
        
        current_min_prices = self.base_min_prices.copy()
        build_log = []
        
        for i, category in enumerate(self.ordered_categories):
            cat_df = get_components_by_category(self.df, category)
            
            if category in ['Motherboard', 'CPU'] and chosen_socket is not None:
                cat_df = cat_df[cat_df['Socket'] == chosen_socket]
            if category == 'RAM' and chosen_ram_type is not None:
                cat_df = cat_df[cat_df['RAM_Type'] == chosen_ram_type]
            if category == 'Power Supply' and total_tdp > 0:
                cat_df = cat_df[cat_df['Power_W'] >= total_tdp + 100]
                
            if cat_df.empty:
                return False, [], 0, 0, 0, []
                
            current_min_prices[category] = cat_df['Price_PLN'].min()

            remaining_cats = self.ordered_categories[i+1:]
            min_cost_of_rest = sum(current_min_prices.get(c, 0) for c in remaining_cats)
            absolute_max = remaining_budget - min_cost_of_rest
            
            if absolute_max < current_min_prices[category]:
                return False, [], 0, 0, 0, []

            current_surplus = remaining_budget - min_cost_of_rest - current_min_prices[category]
            current_weight = weights.get(category, 0.0)
            remaining_weights = sum(weights.get(c, 0.0) for c in self.ordered_categories[i:])
            
            norm_weight = (current_weight / remaining_weights) if remaining_weights > 0 else (1.0 if i == len(self.ordered_categories)-1 else 0.0)
            
            allocated_budget = current_min_prices[category] + (current_surplus * norm_weight)
            safe_max_spend = min(allocated_budget, absolute_max)
            
            affordable_df = filter_by_max_price(cat_df, safe_max_spend)
            
            if affordable_df.empty:
                affordable_df = filter_by_max_price(cat_df, absolute_max)
                
            if affordable_df.empty:
                return False, [], 0, 0, 0, [] 
                
            affordable_df = affordable_df.sort_values(by=['Performance_Score', 'Price_PLN'], ascending=[False, True])
            
            top_k = affordable_df.head(min(3, len(affordable_df)))
            best_component = top_k.sample(n=1).iloc[0]
            
            socket_val = best_component.get('Socket')
            if pd.notna(socket_val) and str(socket_val).lower() != 'nan':
                if chosen_socket is None and category in ['Motherboard', 'CPU']: 
                    chosen_socket = socket_val
                    
            ram_val = best_component.get('RAM_Type')
            if category == 'Motherboard' and pd.notna(ram_val): 
                chosen_ram_type = ram_val
                
            tdp_val = best_component.get('TDP_W')
            if category in ['CPU', 'GPU'] and pd.notna(tdp_val): 
                total_tdp += tdp_val
                
            if category == 'GPU': gpu_score = best_component['Performance_Score']
            if category == 'CPU':
                cpu_score = best_component['Performance_Score']
                if gpu_score > 0 and cpu_score < 0.3 * gpu_score:
                    return False, [], 0, 0, 0, [] 

            components.append(best_component)
            price = best_component['Price_PLN']
            remaining_budget -= price
            total_spent += price
            
            info = f"{category.ljust(12)} | {price:7.2f} PLN | W: {best_component['Performance_Score']:4.0f} | {best_component['Name']}"
            build_log.append(info)

        return True, components, total_spent, remaining_budget, total_tdp, build_log


if __name__ == '__main__':
    try:
        a = float(input("Podaj budzet w PLN: "))
        user_mode = input("1 - Gry, 2 - Praca: ").strip()
        if user_mode not in ['1', '2']: user_mode = '1'
            
        builder = PCBuilder(budget=a, mode=user_mode)
        best_build = builder.build(num_candidates=200)
        
        if best_build:
            print("\n" + "="*70)
            print("NAJLEPSZA ZNALEZIONA KONFIGURACJA")
            print(f"Wynik Algorytmu (Fitness): {best_build['score']}")
            print("="*70)
            for log in best_build['log']:
                print(log)
            print("-" * 70)
            print(f"Suma wydatkow: {best_build['spent']:.2f} PLN z {a:.2f} PLN")
            print(f"Wymagany zasilacz: minimum {best_build['tdp'] + 100}W")
            print("="*70)
        else:
            print("Nie udalo sie zlozyc zbalansowanego zestawu w tym budzecie.")
            
    except ValueError:
        print("Blad: Podana wartosc nie jest poprawna liczba!")