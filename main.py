import pandas as pd
from utils import load_data, get_components_by_category, filter_by_max_price, remove_nan_categories

def build_optimal_pc(budget: float, mode: str):
    df = load_data('dataset.csv')
    if df.empty:
        print("Brak danych do analizy.")
        return
    
    # Konwersja danych z zabezpieczeniem
    df['Price_PLN'] = pd.to_numeric(df['Price_PLN'], errors='coerce')
    df['Performance_Score'] = pd.to_numeric(df['Performance_Score'], errors='coerce')
    df['TDP_W'] = pd.to_numeric(df['TDP_W'], errors='coerce')
    df['Power_W'] = pd.to_numeric(df['Power_W'], errors='coerce')
    
    df = remove_nan_categories(df, column='Category')
    categories = list(df['Category'].unique())
    
    # Pobieramy bazowe minimalne ceny dla każdej kategorii
    base_min_prices = {}
    for cat in categories:
        base_min_prices[cat] = df[df['Category'] == cat]['Price_PLN'].min()
        
    total_min_cost = sum(base_min_prices.values())
    if budget < total_min_cost:
        print(f"Za mały budżet! Z najtańszych części komputer kosztuje minimum: {total_min_cost:.2f} PLN")
        return

    priority_order = ['GPU', 'CPU', 'Motherboard', 'RAM', 'Storage', 'Power Supply']
    for c in categories:
        if c not in priority_order:
            priority_order.append(c)
            
    ordered_categories = [c for c in priority_order if c in categories]
    
    # 1. PROFILE: Inicjalne wagi w zależności od celu komputera
    if mode == '2': # Praca (Mocny CPU i dużo RAM)
        weights = {'CPU': 0.40, 'RAM': 0.20, 'Motherboard': 0.15, 'Storage': 0.10, 'GPU': 0.10, 'Power Supply': 0.05}
    else:           # Gry (Domyślnie - Mocne GPU)
        weights = {'GPU': 0.45, 'CPU': 0.25, 'Motherboard': 0.10, 'RAM': 0.08, 'Storage': 0.07, 'Power Supply': 0.05}

    # 3. ANTY-BOTTLENECK: Pętla samokorygująca (max 4 próby złożenia idealnego zestawu)
    MAX_ATTEMPTS = 4
    for attempt in range(MAX_ATTEMPTS):
        selected_components = []
        total_spent = 0
        remaining_budget = budget
        chosen_socket = None
        chosen_ram_type = None
        total_tdp = 0
        
        gpu_score = 0
        cpu_score = 0
        bottleneck_detected = False
        
        current_min_prices = base_min_prices.copy()
        build_log = [] # Zapisujemy logi, by nie śmiecić w konsoli podczas powtórek algorytmu
        
        for i, category in enumerate(ordered_categories):
            cat_df = get_components_by_category(df, category)
            
            # Zabezpieczenie kompatybilności Socketu
            if category in ['Motherboard', 'CPU'] and chosen_socket is not None:
                cat_df = cat_df[cat_df['Socket'] == chosen_socket]
                if not cat_df.empty:
                    current_min_prices[category] = cat_df['Price_PLN'].min()
                    
            # 2a. Zabezpieczenie kompatybilności RAM
            if category == 'RAM' and chosen_ram_type is not None:
                cat_df = cat_df[cat_df['RAM_Type'] == chosen_ram_type]
                
            # 2b. Zabezpieczenie Zasilacza (PSU) - dodajemy zapas 100W do TDP
            if category == 'Power Supply' and total_tdp > 0:
                required_power = total_tdp + 100
                cat_df = cat_df[cat_df['Power_W'] >= required_power]

            remaining_categories = ordered_categories[i+1:]
            min_cost_of_rest = sum(current_min_prices.get(c, 0) for c in remaining_categories)
            
            current_surplus = remaining_budget - min_cost_of_rest
            current_weight = weights.get(category, 0.0)
            remaining_weights = sum(weights.get(c, 0.0) for c in ordered_categories[i:])
            
            if remaining_weights > 0:
                normalized_weight = current_weight / remaining_weights
            else:
                normalized_weight = 1.0 if i == len(ordered_categories) - 1 else 0.0
                
            category_surplus = current_surplus * normalized_weight
            allocated_budget = current_min_prices.get(category, 0) + category_surplus
            
            absolute_max = remaining_budget - min_cost_of_rest
            safe_max_spend = min(allocated_budget, absolute_max)
            
            affordable_df = filter_by_max_price(cat_df, safe_max_spend)
            if affordable_df.empty:
                affordable_df = filter_by_max_price(cat_df, absolute_max)
                
            if affordable_df.empty:
                build_log.append(f"[-] Nie udało się dobrać elementu: {category}")
                continue
                
            affordable_df = affordable_df.sort_values(by=['Performance_Score', 'Price_PLN'], ascending=[False, True])
            best_component = affordable_df.iloc[0]
            
            # --- ZAPISYWANIE DANYCH DO ZABEZPIECZEŃ NA KOLEJNE KROKI ---
            socket_val = best_component.get('Socket')
            if pd.notna(socket_val) and str(socket_val).strip() != '' and str(socket_val).lower() != 'nan':
                if chosen_socket is None and category in ['Motherboard', 'CPU']:
                    chosen_socket = socket_val
                    
            ram_val = best_component.get('RAM_Type')
            if category == 'Motherboard' and pd.notna(ram_val):
                chosen_ram_type = ram_val
                
            tdp_val = best_component.get('TDP_W')
            if category in ['CPU', 'GPU'] and pd.notna(tdp_val):
                total_tdp += tdp_val
                
            # Sprawdzanie wydajności pod kątem Bottlenecku
            if category == 'GPU':
                gpu_score = best_component['Performance_Score']
            if category == 'CPU':
                cpu_score = best_component['Performance_Score']
                # Uznajemy za bottleneck, jeśli CPU ma mniej niż 50% wydajności GPU
                if gpu_score > 0 and cpu_score < 0.5 * gpu_score:
                    bottleneck_detected = True

            # Aktualizacja portfela
            selected_components.append(best_component)
            price = best_component['Price_PLN']
            remaining_budget -= price
            total_spent += price
            
            # Zapisywanie logów
            display_socket = str(socket_val) if pd.notna(socket_val) and str(socket_val).lower() != 'nan' else 'Brak'
            display_ram = str(ram_val) if pd.notna(ram_val) and str(ram_val).lower() != 'nan' else 'Brak'
            
            info = f"[+] Dobrano {category}: {best_component['Name']}\n    Cena: {price:.2f} PLN | Wydajność: {best_component['Performance_Score']}"
            if display_socket != 'Brak': info += f" | Socket: {display_socket}"
            if category in ['Motherboard', 'RAM'] and display_ram != 'Brak': info += f" | RAM: {display_ram}"
            build_log.append(info)
            
        # --- KONIEC ITERACJI SKŁADANIA ---
        
        # Jeśli wykryto Bottleneck, zabieramy 5% budżetu z GPU na rzecz CPU i resetujemy pętlę
        if bottleneck_detected and mode == '1' and attempt < MAX_ATTEMPTS - 1:
            print(f"[*] Algorytm (Próba {attempt+1}): Wykryto Bottleneck (Słaby CPU w stosunku do GPU). Optymalizuję przydział budżetu...")
            weights['GPU'] -= 0.05
            weights['CPU'] += 0.05
            continue 
            
        # Jeśli wszystko jest OK , wypisujemy wynik i kończymy
        print(f"\n==== Zestaw Komputerowy (Sukces po {attempt+1} iteracjach) ====")
        for log in build_log:
            print(log)
            
        print(f"\n==== Podsumowanie ============================")
        print(f"Wydano: {total_spent:.2f} PLN z {budget:.2f} PLN.")
        print(f"Wolne środki: {remaining_budget:.2f} PLN.")
        if total_tdp > 0:
            print(f"Zapotrzebowanie energetyczne: {total_tdp}W (Zasilacz dobrany z ok. 100W zapasem)")
        break

if __name__ == '__main__':
    try:
        a = float(input("Podaj budżet w PLN: "))
        
        print("\nDo czego ma służyć ten komputer?")
        print("1 - Gry (Priorytet na kartę graficzną)")
        print("2 - Praca/Programowanie (Priorytet na procesor i RAM)")
        user_mode = input("Wybierz opcję (1 lub 2): ").strip()
        
        if user_mode not in ['1', '2']:
            print("Niepoprawny wybór. Domyślnie wybrano: 1 - Gry.")
            user_mode = '1'
            
        build_optimal_pc(budget=a, mode=user_mode)
    except ValueError:
        print("Błąd: Podana wartość nie jest poprawną liczbą!")