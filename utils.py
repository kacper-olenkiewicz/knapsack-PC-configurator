import pandas as pd
import numpy as np

def load_data(filepath: str = 'dataset.csv') -> pd.DataFrame:
    #Wczytuje dane o podzespołach z pliku CSV.
    try:
        df = pd.read_csv(filepath)
        return df
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku {filepath}")
        return pd.DataFrame()

def get_components_by_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    #Zwraca podzespoły z określonej kategorii (np. CPU, GPU).
    return df[df['Category'] == category]

def filter_by_max_price(df: pd.DataFrame, max_price: float) -> pd.DataFrame:
    #Zwraca podzespoły, których cena nie przekracza podanej kwoty.
    return df[df['Price_PLN'] <= max_price]

def get_best_performance_per_price(df: pd.DataFrame) -> pd.DataFrame:
    #Oblicza stosunek wydajności do ceny i sortuje od najbardziej opłacalnych.
    # Kopia, aby uniknąć ostrzeżenia SettingWithCopyWarning
    df_calc = df.copy()
    df_calc['Value_Score'] = df_calc['Performance_Score'] / df_calc['Price_PLN']
    return df_calc.sort_values(by='Value_Score', ascending=False)

def remove_nan_categories(df: pd.DataFrame, column: str = 'Category') -> pd.DataFrame:
    #Usuwano puste wartości dla danej kategorii/kolumny np. NaN.
    return df.dropna(subset=[column])

