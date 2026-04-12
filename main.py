import random

import pandas as pd

from utils import load_data, remove_nan_categories


def _safe_str(value) -> str:
    if pd.isna(value):
        return ''
    return str(value).strip()


def _evaluate_solution(df: pd.DataFrame, categories: list[str], harmony: list[int], budget: float) -> tuple[float, dict]:
    selected = [df.loc[harmony[i]] for i in range(len(categories))]
    total_price = float(sum(float(row['Price_PLN']) for row in selected))
    total_perf = float(sum(float(row['Performance_Score']) for row in selected))

    penalty = 0.0

    row_by_cat = {categories[i]: selected[i] for i in range(len(categories))}

    cpu = row_by_cat.get('CPU')
    mobo = row_by_cat.get('Motherboard')
    ram = row_by_cat.get('RAM')
    gpu = row_by_cat.get('GPU')
    psu = row_by_cat.get('Power Supply')

    if cpu is not None and mobo is not None:
        if _safe_str(cpu.get('Socket')) != _safe_str(mobo.get('Socket')):
            penalty += 2000.0

    if mobo is not None and ram is not None:
        mobo_ram = _safe_str(mobo.get('RAM_Type'))
        ram_type = _safe_str(ram.get('RAM_Type'))
        if mobo_ram and ram_type and mobo_ram != ram_type:
            penalty += 1200.0

    if psu is not None:
        cpu_tdp = float(cpu.get('TDP_W')) if cpu is not None and pd.notna(cpu.get('TDP_W')) else 0.0
        gpu_tdp = float(gpu.get('TDP_W')) if gpu is not None and pd.notna(gpu.get('TDP_W')) else 0.0
        psu_power = float(psu.get('Power_W')) if pd.notna(psu.get('Power_W')) else 0.0
        required_power = cpu_tdp + gpu_tdp + 150.0
        if psu_power < required_power:
            penalty += 1500.0 + (required_power - psu_power)

    if total_price > budget:
        penalty += (total_price - budget) * 2.5

    budget_utilization_bonus = (1.0 - abs(budget - total_price) / budget) * 15.0 if budget > 0 else 0.0

    fitness = total_perf + budget_utilization_bonus - penalty
    details = {
        'selected': selected,
        'total_price': total_price,
        'total_perf': total_perf,
        'penalty': penalty,
        'fitness': fitness,
    }
    return fitness, details


def build_optimal_pc_harmony(
    budget: float,
    harmony_memory_size: int = 4000,
    iterations: int = 40000,
    hmcr: float = 0.60,
    par: float = 0.25,
):
    df = load_data('dataset.csv')
    if df.empty:
        print('Brak danych do analizy.')
        return

    df = remove_nan_categories(df, column='Category').copy()
    df['Price_PLN'] = pd.to_numeric(df['Price_PLN'], errors='coerce')
    df['Performance_Score'] = pd.to_numeric(df['Performance_Score'], errors='coerce')
    df = df.dropna(subset=['Price_PLN', 'Performance_Score'])

    categories = sorted(df['Category'].unique().tolist())
    if not categories:
        print('Brak kategorii w danych.')
        return

    candidate_indices: dict[str, list[int]] = {}
    for category in categories:
        cat_df = df[df['Category'] == category].copy()
        cat_df['Value_Score'] = cat_df['Performance_Score'] / cat_df['Price_PLN']
        cat_df = cat_df.sort_values(by='Value_Score', ascending=False)
        candidate_indices[category] = cat_df.index.tolist()
        if not candidate_indices[category]:
            print(f'Brak kandydatow dla kategorii: {category}')
            return

    def random_harmony() -> list[int]:
        return [random.choice(candidate_indices[category]) for category in categories]

    harmony_memory: list[tuple[list[int], float, dict]] = []
    for _ in range(harmony_memory_size):
        h = random_harmony()
        fitness, details = _evaluate_solution(df, categories, h, budget)
        harmony_memory.append((h, fitness, details))

    for _ in range(iterations):
        new_harmony = []
        for i, category in enumerate(categories):
            choices = candidate_indices[category]

            if random.random() < hmcr:
                base_harmony = random.choice(harmony_memory)[0]
                picked_index = base_harmony[i]
            else:
                picked_index = random.choice(choices)

            if random.random() < par:
                pos = choices.index(picked_index) if picked_index in choices else random.randrange(len(choices))
                direction = random.choice([-1, 1])
                pos = max(0, min(len(choices) - 1, pos + direction))
                picked_index = choices[pos]

            new_harmony.append(picked_index)

        new_fitness, new_details = _evaluate_solution(df, categories, new_harmony, budget)
        worst_idx = min(range(len(harmony_memory)), key=lambda idx: harmony_memory[idx][1])

        if new_fitness > harmony_memory[worst_idx][1]:
            harmony_memory[worst_idx] = (new_harmony, new_fitness, new_details)
        
        if(_ == iterations//3):
            hmcr += 0.15
        if(_ == iterations//1.5):
            hmcr += 0.15

    best_harmony, _, best_details = max(harmony_memory, key=lambda x: x[1])

    print('\n==== Najlepszy zestaw (Harmony Search) =======')
    for i, category in enumerate(categories):
        row = df.loc[best_harmony[i]]
        socket = _safe_str(row.get('Socket')) or 'Brak'
        print(f"[+] {category}: {row['Name']}")
        print(
            f"    Cena: {float(row['Price_PLN']):.2f} PLN | "
            f"Wydajnosc: {float(row['Performance_Score']):.2f} | "
            f"Socket: {socket}"
        )

    total_price = best_details['total_price']
    print('\n==== Podsumowanie ============================')
    print(f'Wydano: {total_price:.2f} PLN z {budget:.2f} PLN.')
    print(f"Wolne srodki: {budget - total_price:.2f} PLN.")
    print(f"Suma wydajnosci: {best_details['total_perf']:.2f}")
    print(f"Kara za ograniczenia: {best_details['penalty']:.2f}")


if __name__ == '__main__':
    build_optimal_pc_harmony(budget=3000.0)
