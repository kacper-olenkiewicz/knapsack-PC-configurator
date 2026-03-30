from flask import Flask, request, render_template_string
import pandas as pd
from main import PCBuilder 

app = Flask(__name__)

HTML_BASE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kreator PC</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f9f9f9;}
        nav { margin-bottom: 20px; background-color: #333; padding: 10px; border-radius: 5px; }
        nav a { margin-right: 15px; text-decoration: none; color: white; font-weight: bold;}
        nav a:hover { color: #ddd; }
        .container { background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #f2f2f2; }
        .form-group { margin-bottom: 15px; }
        input, select, button { padding: 8px; margin-top: 5px; }
        button { background-color: #28a745; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #218838; }
    </style>
</head>
<body>
    <nav>
        <a href="/">Wybierz podzespoly</a>
        <a href="/baza">Baza komponentow</a>
    </nav>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

HTML_INDEX = HTML_BASE.replace('{% block content %}{% endblock %}', """
<h2>Kreator zestawu komputerowego</h2>
<form method="POST">
    <div class="form-group">
        <label>Podaj budzet (PLN):</label><br>
        <input type="number" name="budget" required value="{{ request.form.budget if request.form.budget else 5000 }}">
    </div>
    <div class="form-group">
        <label>Tryb zestawu:</label><br>
        <select name="mode">
            <option value="1" {% if request.form.mode == '1' %}selected{% endif %}>Gry</option>
            <option value="2" {% if request.form.mode == '2' %}selected{% endif %}>Praca</option>
        </select>
    </div>
    <button type="submit">Generuj zestaw</button>
</form>

{% if result %}
    <hr>
    <h3>Konfiguracja koncowa</h3>
    <p><strong>Wydajnosc calkowita:</strong> {{ result.score }}</p>
    <p><strong>Wydano:</strong> {{ "%.2f"|format(result.spent) }} PLN z {{ budget }} PLN</p>
    <p><strong>Wymagany zasilacz:</strong> {{ result.tdp + 100 }} W</p>
    
    <table>
        <tr>
            <th>Kategoria</th>
            <th>Nazwa</th>
            <th>Cena (PLN)</th>
            <th>Wydajnosc</th>
        </tr>
        {% for comp in result.components %}
        <tr>
            <td>{{ comp.Category }}</td>
            <td>{{ comp.Name }}</td>
            <td>{{ comp.Price_PLN }}</td>
            <td>{{ comp.Performance_Score }}</td>
        </tr>
        {% endfor %}
    </table>
{% elif error %}
    <hr>
    <p style="color: red; font-weight: bold;">{{ error }}</p>
{% endif %}
""")

HTML_DB = HTML_BASE.replace('{% block content %}{% endblock %}', """
<h2>Dostepna baza danych (dataset.csv)</h2>
{% for category, items in data.items() %}
    <h3>{{ category }}</h3>
    <table>
        <tr>
            <th>Nazwa</th>
            <th>Cena (PLN)</th>
            <th>Wydajnosc</th>
            <th>Socket</th>
            <th>Typ RAM</th>
            <th>TDP (W)</th>
            <th>Pobor Mocy (W)</th>
        </tr>
        {% for item in items %}
        <tr>
            <td>{{ item.Name }}</td>
            <td>{{ item.Price_PLN }}</td>
            <td>{{ item.Performance_Score }}</td>
            <td>{{ item.Socket }}</td>
            <td>{{ item.RAM_Type }}</td>
            <td>{{ item.TDP_W }}</td>
            <td>{{ item.Power_W }}</td>
        </tr>
        {% endfor %}
    </table>
{% endfor %}
""")

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    budget = None
    
    if request.method == 'POST':
        try:
            budget = float(request.form['budget'])
            mode = request.form['mode']
            
            # Polaczenie z algorytmem z pliku main.py
            builder = PCBuilder(budget=budget, mode=mode)
            result = builder.build(num_candidates=200)
            
            if not result:
                error = "Algorytm nie znalazl zbalansowanego zestawu dla podanego budzetu. Sprobuj zwiekszyc kwote."
        except Exception as e:
            error = f"Wystapil blad krytyczny: {str(e)}"
            
    return render_template_string(HTML_INDEX, result=result, error=error, budget=budget)

@app.route('/baza')
def database():
    try:
        df = pd.read_csv('dataset.csv')
        df = df.fillna('-')
        
        data_grouped = {}
        for category in df['Category'].unique():
            if pd.notna(category) and category != '-':
                cat_items = df[df['Category'] == category].to_dict('records')
                data_grouped[category] = cat_items
                
        return render_template_string(HTML_DB, data=data_grouped)
    except Exception as e:
        return f"Wystapil blad podczas wczytywania bazy danych: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)