import pandas as pd
from utils import load_data, get_components_by_category, filter_by_max_price, remove_nan_categories

def build_optimal_pc(budget: float):
    df = load_data('dataset.csv')
    if df.empty:
        print("Brak danych do analizy.")
        return
    
    # Usuwamy wiersze, w których "Category" jest NaN
    df = remove_nan_categories(df, column='Category')
    categories = list(df['Category'].unique())
    
    # Aby poprawnie dysponować budżetem, musimy ustalić rezerwę na pozostałe części.
    # W pierwszej kolejności obliczamy minimalne kwoty, jakie trzeba wydać na każdą z kategorii.
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
    
    print(f"==== Planowanie zestawu komputerowego. Całkowity budżet: {budget:.2f} PLN ====\n")
    
    # Sortujemy kategorie. Najpierw kupujemy najdroższe i kluczowe części, gdzie warto "wtłoczyć" jak najwięcej budżetu.
    priority_order = ['GPU', 'CPU', 'Motherboard', 'RAM', 'Storage', 'Power Supply']
    
    # Dodajemy ewentualne inne kategorie z bazy, o których zapomnieliśmy
    for c in categories:
        if c not in priority_order:
            priority_order.append(c)
            
    # Filtrujemy tylko te kategorie, które rzeczywiście wystepują w naszej bazie
    ordered_categories = [c for c in priority_order if c in categories]
    
    # Nowy, lepszy algorytm
    for i, category in enumerate(ordered_categories):
        cat_df = get_components_by_category(df, category)
        
        # Filtrujemy dane w przypadku CPU/Motherboard dla zachowania kompatybilności gniazda
        if category in ['Motherboard', 'CPU'] and chosen_socket is not None:
            cat_df = cat_df[cat_df['Socket'] == chosen_socket]
            
            # Aktualizacja minimalnej ceny płyty po nałożeniu ograniczenia socketu, 
            # na wypadek gdyby ten socket wymagał nieco droższej części w koszyku
            if not cat_df.empty:
                min_prices[category] = cat_df['Price_PLN'].min()

        # Obliczamy ile mamy "bezpiecznego" budżetu dla TEJ kategorii.
        # Od pozostałych pieniędzy odejmujemy absolutne minimum, które będziemy musieli wydać na to co zostało do kupienia
        remaining_categories = ordered_categories[i+1:]
        min_cost_of_rest = sum(min_prices.get(c, 0) for c in remaining_categories)
        
        safe_max_spend = remaining_budget - min_cost_of_rest
        
        affordable_df = filter_by_max_price(cat_df, safe_max_spend)
        
        if affordable_df.empty:
            print(f"[-] Nie udało się dobrać elementu z kategorii: {category} (Niewystarczający budżet np. dla socketu: {chosen_socket})")
            continue
            
        # Zamiast patrzeć tylko na "value", sortujemy tak, aby wyciągnąć JAK NAJWYŻSZĄ WYDAJNOŚĆ w naszym wyznaczonym bezpiecznym budżecie. 
        # Cechą drugorzędną (w przypadku remisu) jest cena - weźmiemy stąd najtańszy o danej mocnej wydajności.
        affordable_df = affordable_df.sort_values(by=['Performance_Score', 'Price_PLN'], ascending=[False, True])
        best_component = affordable_df.iloc[0]
        
        socket_val = best_component.get('Socket')
        
        # Oznaczmy zapisany socket dla celów kompatybilności w kolejnych iteracjach
        if pd.notna(socket_val) and str(socket_val).strip() != '' and str(socket_val).lower() != 'nan':
            if chosen_socket is None and category in ['Motherboard', 'CPU']:
                chosen_socket = socket_val
        
        # Aktualizacja portfela i koszyka
        selected_components.append(best_component)
        price = best_component['Price_PLN']
        remaining_budget -= price
        total_spent += price
        
        # Czysty format wyświetlania złącza, pozbywający się "nan"
        display_socket = str(socket_val) if pd.notna(socket_val) and str(socket_val).lower() != 'nan' else 'Brak'
        
        print(f"[+] Dobrano {category}: {best_component['Name']}")
        print(f"    Cena: {price:.2f} PLN | Wynik Wydajności: {best_component['Performance_Score']} | Socket: {display_socket}")
        
    print(f"\n==== Podsumowanie ============================")
    print(f"Wydano: {total_spent:.2f} PLN z {budget:.2f} PLN.")
    print(f"Wolne środki: {remaining_budget:.2f} PLN.")

if __name__ == '__main__':
    # Przykładowe wywołanie z budżetem 5000 zł
    build_optimal_pc(budget=5000.0)
