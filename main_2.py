import pandas as pd
from utils import load_data

def get_pareto_front(state_list):
    """
    Filtruje listę stanów tylko do tych na froncie Pareto, używając kubełkowania.
    Dzięki temu unikamy eksplozji stanów (tzw. "out of memory" / bardzo długa praca).
    """
    grouped = {}
    for state in state_list:
        cost, perf, items, constraints = state
        
        # Agregacja po zaokrąglonym koszcie (do 1 PLN), żeby drastycznie zredukować liczbę stanów
        cost_int = int(cost)
        
        # Agregacja TDP do pełnych dziesiątek (przy zasilaczu precyzja do 1W nie ma absolutnie znaczenia)
        s, r, t = constraints
        t_rounded = int(t / 10) * 10 
        new_constraints = (s, r, t_rounded)
        
        if new_constraints not in grouped:
            grouped[new_constraints] = {}
            
        if cost_int not in grouped[new_constraints]:
            grouped[new_constraints][cost_int] = state
        else:
            # Zachowuj tylko stan o największej wydajności w danej cenie i grupie wymagań
            if perf > grouped[new_constraints][cost_int][1]:
                grouped[new_constraints][cost_int] = state
                
    result = []
    for new_constraints, cost_dict in grouped.items():
        # Tradycyjny front Pareto wewnątrz danej grupy tolerancji
        sorted_costs = sorted(cost_dict.keys())
        
        pareto = []
        max_perf_so_far = -1
        for cost_int in sorted_costs:
            state = cost_dict[cost_int]
            perf = state[1]
            if perf > max_perf_so_far:
                pareto.append(state)
                max_perf_so_far = perf
                
        result.extend(pareto)
        
    return result

def build_optimal_pc_knapsack(budget: float):
    df = load_data('dataset.csv')
    if df.empty:
        print("Brak danych do analizy.")
        return
        
    df['Price_PLN'] = pd.to_numeric(df['Price_PLN'], errors='coerce')
    df['Performance_Score'] = pd.to_numeric(df['Performance_Score'], errors='coerce')
    df['TDP_W'] = pd.to_numeric(df['TDP_W'], errors='coerce').fillna(0)
    df['Power_W'] = pd.to_numeric(df['Power_W'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Category', 'Price_PLN', 'Performance_Score'])
    
    states = [(0.0, 0.0, (), (None, None, 0.0))]
    
    category_order = [
        ('CPU', 'CPU'),
        ('Motherboard', 'MB'),
        ('RAM', 'RAM'),
        ('Storage', 'STORAGE'),
        ('GPU', 'GPU'),
        ('Power Supply', 'PSU')
    ]
    
    # Pre-konwersja do słowników Pythona - operacje na DF bezpośrednio w pętli powodowały powolne działanie
    category_items = {}
    for cat_name, step_id in category_order:
        cat_df = df[df['Category'] == cat_name]
        category_items[step_id] = cat_df.to_dict('records')
    
    for cat_name, step_id in category_order:
        items_list = category_items.get(step_id, [])
        if not items_list:
            print(f"Brak części w kategorii {cat_name}!")
            return
            
        new_states = []
        
        for state in states:
            curr_cost, curr_perf, curr_items, reqs = state
            socket_req, ram_req, tdp_req = reqs
            
            for item in items_list:
                # Odrzucanie komponentów, które nie pasują konstrukcyjnie
                if step_id == 'MB' and item.get('Socket') != socket_req:
                    continue
                if step_id == 'RAM' and item.get('RAM_Type') != ram_req:
                    continue
                if step_id == 'PSU' and item.get('Power_W', 0) < (tdp_req + 50):
                    continue
                    
                item_cost = item['Price_PLN']
                new_cost = curr_cost + item_cost
                
                # Budżet
                if new_cost > budget:
                    continue
                    
                new_perf = curr_perf + item['Performance_Score']
                new_items_tuple = curr_items + (item,)
                
                # Przygotowywanie ograniczeń dla kolejnych etapów
                # Super ważna optymalizacja: zrzucamy ograniczenia, gdy nie są już potrzebne!
                n_socket, n_ram, n_tdp = socket_req, ram_req, tdp_req
                
                if step_id == 'CPU':
                    n_socket = item.get('Socket')
                    n_tdp += item.get('TDP_W', 0)
                elif step_id == 'MB':
                    n_ram = item.get('RAM_Type')
                    n_socket = None # Socket nie jest już później potrzebny (oczyszczanie przestrzeni stanów)
                elif step_id == 'RAM':
                    n_ram = None    # RAM_Type nie jest już później potrzebny
                elif step_id == 'GPU':
                    n_tdp += item.get('TDP_W', 0)
                    
                new_states.append((new_cost, new_perf, new_items_tuple, (n_socket, n_ram, n_tdp)))
                
        if not new_states:
            print(f"Brak połączalnych konfiguracji po przejściu kategorii: {cat_name}.")
            return
            
        states = get_pareto_front(new_states)
        print(f"[{cat_name}] Konfiguracji po optymalizacji: {len(states)}")
        
    best_state = max(states, key=lambda x: x[1])
    
    total_cost, total_perf, best_items, _ = best_state
    
    print("\n==== OPTYMALNY ZESTAW PC (ALGORITHM KNAPSACK / DP) ====")
    for item in best_items:
        s = item.get('Socket', '')
        r = item.get('RAM_Type', '')
        t = item.get('TDP_W', 0)
        p = item.get('Power_W', 0)
        
        info = f"- {item['Category']:<12}: {item['Name']:<20} | Cena: {item['Price_PLN']:>7.2f} PLN | Wydajność: {item['Performance_Score']}"
        if item['Category'] == 'CPU': info += f" | Socket: {s} | TDP: {t}W"
        if item['Category'] == 'Motherboard': info += f" | Socket: {s} | RAM: {r}"
        if item['Category'] == 'RAM': info += f" | Rodzaj: {r}"
        if item['Category'] == 'GPU': info += f" | TDP: {t}W"
        if item['Category'] == 'Power Supply': info += f" | Moc: {p}W"
        print(info)
        
    print("=========================================================")
    print(f"Sumaryczny koszt  : {total_cost:.2f} PLN z {budget:.2f} PLN budżetu.")
    print(f"Łączna wydajność  : {total_perf:.1f} punktów.")
    print(f"Wolne środki      : {(budget - total_cost):.2f} PLN.")

if __name__ == '__main__':
    try:
        a = float(input("Podaj budżet: "))
        build_optimal_pc_knapsack(budget=a)
    except ValueError:
        print("Błąd: Podana wartość nie jest poprawną liczbą!")