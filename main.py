import pandas as pd
from utils import load_data, get_components_by_category, filter_by_max_price, remove_nan_categories

def build_optimal_pc(budget: float):
    df = load_data('dataset.csv')
    if df.empty:
        print("Brak danych do analizy.")
        return
    
    # 1. Zabezpieczenie: Wymuszamy typ liczbowy, by sortowanie i filtry działały poprawnie!
    df['Price_PLN'] = pd.to_numeric(df['Price_PLN'], errors='coerce')
    df['Performance_Score'] = pd.to_numeric(df['Performance_Score'], errors='coerce')
    
    # Usuwamy wiersze, w których "Category" jest NaN
    df = remove_nan_categories(df, column='Category')
    categories = list(df['Category'].unique())
    
    min_prices = {}
    for cat in categories:
        min_prices[cat] = df[df['Category'] == cat]['Price_PLN'].min()
        
    total_min_cost = sum(min_prices.values())
    if budget < total_min_cost:
        print(f"Za mały budżet! Z najtańszych części komputer kosztuje minimum: {total_min_cost:.2f} PLN")
        return

    selected_components = []
    total_spent = 0
    remaining_budget = budget
    chosen_socket = None
    
    priority_order = ['GPU', 'CPU', 'Motherboard', 'RAM', 'Storage', 'Power Supply']
    for c in categories:
        if c not in priority_order:
            priority_order.append(c)
            
    ordered_categories = [c for c in priority_order if c in categories]
    
    # 2.Proporcje, według których rozdzielamy NADWYŻKĘ budżetu
    weights = {
        'GPU': 0.45,
        'CPU': 0.25,
        'Motherboard': 0.10,
        'RAM': 0.08,
        'Storage': 0.07,
        'Power Supply': 0.05
    }
    
    for i, category in enumerate(ordered_categories):
        cat_df = get_components_by_category(df, category)
        
        if category in ['Motherboard', 'CPU'] and chosen_socket is not None:
            cat_df = cat_df[cat_df['Socket'] == chosen_socket]
            if not cat_df.empty:
                min_prices[category] = cat_df['Price_PLN'].min()

        remaining_categories = ordered_categories[i+1:]
        min_cost_of_rest = sum(min_prices.get(c, 0) for c in remaining_categories)
        
        # Obliczamy ile mamy "wolnych środków" ponad absolutne minimum na resztę części
        current_surplus = remaining_budget - min_cost_of_rest
        
        # Obliczamy zbalansowany przydział z nadwyżki dla obecnej kategorii
        current_weight = weights.get(category, 0.0)
        remaining_weights = sum(weights.get(c, 0.0) for c in ordered_categories[i:])
        
        if remaining_weights > 0:
            normalized_weight = current_weight / remaining_weights
        else:
            normalized_weight = 1.0 if i == len(ordered_categories) - 1 else 0.0
            
        category_surplus = current_surplus * normalized_weight
        
        # Budżet na część = jej cena minimalna + jej kawałek nadwyżki
        allocated_budget = min_prices.get(category, 0) + category_surplus
        
        # Zabezpieczenie przed przekroczeniem fizycznie dostępnych pieniędzy
        absolute_max = remaining_budget - min_cost_of_rest
        safe_max_spend = min(allocated_budget, absolute_max)
        
        affordable_df = filter_by_max_price(cat_df, safe_max_spend)
        
        # Ratunek: Jeśli proporcjonalny budżet jest za mały (np. przez wymogi socketu), 
        # zezwalamy na wydanie wszystkiego co można (absolute_max)
        if affordable_df.empty:
            affordable_df = filter_by_max_price(cat_df, absolute_max)
            
        if affordable_df.empty:
            print(f"[-] Nie udało się dobrać elementu z kategorii: {category} (Niewystarczający budżet np. dla socketu: {chosen_socket})")
            continue
            
        # Wybieramy najwydajniejszą część w ustalonym, abalansowanym budżecie
        affordable_df = affordable_df.sort_values(by=['Performance_Score', 'Price_PLN'], ascending=[False, True])
        best_component = affordable_df.iloc[0]
        
        socket_val = best_component.get('Socket')
        if pd.notna(socket_val) and str(socket_val).strip() != '' and str(socket_val).lower() != 'nan':
            if chosen_socket is None and category in ['Motherboard', 'CPU']:
                chosen_socket = socket_val
        
        selected_components.append(best_component)
        price = best_component['Price_PLN']
        remaining_budget -= price
        total_spent += price
        
        display_socket = str(socket_val) if pd.notna(socket_val) and str(socket_val).lower() != 'nan' else 'Brak'
        
        print(f"[+] Dobrano {category}: {best_component['Name']}")
        print(f"    Cena: {price:.2f} PLN | Wynik Wydajności: {best_component['Performance_Score']} | Socket: {display_socket}")
        
    print(f"\n==== Podsumowanie ============================")
    print(f"Wydano: {total_spent:.2f} PLN z {budget:.2f} PLN.")
    print(f"Wolne środki: {remaining_budget:.2f} PLN.")

if __name__ == '__main__':
    try:
        a = float(input("Podaj budżet: "))
        build_optimal_pc(budget=a)
    except ValueError:
        print("Błąd: Podana wartość nie jest poprawną liczbą!")