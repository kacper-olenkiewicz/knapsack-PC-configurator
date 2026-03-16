import pandas as pd
from utils import load_data, get_components_by_category, filter_by_max_price, get_best_performance_per_price, remove_nan_categories

def build_optimal_pc(budget: float):
    df = load_data('dataset.csv')
    if df.empty:
        print("Brak danych do analizy.")
        return
    
    # 1. wyrzucamy z setu te dane, gdzie 'Category' to NaN/null
    df = remove_nan_categories(df, column='Category')
    
    # Wyciągnijmy wszystkie dostępne kategorie w pliku
    categories = df['Category'].unique()
    
    selected_components = []
    total_spent = 0
    remaining_budget = budget
    
    # Zmienna przechowująca nasz socket procesora/płyty
    chosen_socket = None
    
    # Główna pętla przez kategorie 
    for category in categories:
        cat_df = get_components_by_category(df, category)
        
        # Filtrujemy ze względu na wymóg zgodności socketu pomiędzy CPU a Płytą
        if category in ['Motherboard', 'CPU'] and chosen_socket is not None:
            cat_df = cat_df[cat_df['Socket'] == chosen_socket]
        
        # Odrzucamy to na co nas już nie stać
        affordable_df = filter_by_max_price(cat_df, remaining_budget)
        
        if affordable_df.empty:
            print(f"[-] Nie udało się dobrać elementu z kategorii: {category}")
            if category in ['Motherboard', 'CPU']:
               print(f"    (Przyczyna: Brak zgodności w budżecie dla socketu: {chosen_socket})")
            continue
            
        # Wybieramy najwydajniejszy i najbardziej odpowiedni z tanich
        best_value_df = get_best_performance_per_price(affordable_df)
        best_component = best_value_df.iloc[0]
        
        # Zapisujemy nasz Socket, jeśli właśnie na niego trafliśmy, żeby następna część z niego korzystała
        if pd.notna(best_component.get('Socket')) and str(best_component.get('Socket')).strip() != '':
            if chosen_socket is None and category in ['Motherboard', 'CPU']:
                chosen_socket = best_component['Socket']
        
        # Aktualizacja portfela i koszyka
        selected_components.append(best_component)
        price = best_component['Price_PLN']
        remaining_budget -= price
        total_spent += price
        
        print(f"[+] Dobrano {category}: {best_component['Name']}")
        print(f"    Cena: {price:.2f} PLN | Wynik Wydajności: {best_component['Performance_Score']} | Socket: {best_component.get('Socket', 'Brak')}")
        
    print(f"\n==== Podsumowanie ============================")
    print(f"Wydano: {total_spent:.2f} PLN z {budget:.2f} PLN.")
    print(f"Wolne środki: {remaining_budget:.2f} PLN.")

if __name__ == '__main__':
    build_optimal_pc(budget=5000.0)
