import pandas as pd
import random

SOCKETS = ['AM4', 'AM5', 'LGA1200', 'LGA1700', 'LGA1851']
RAM_TYPES = ['DDR4', 'DDR5']
FORM_FACTORS = ['ATX', 'Micro-ATX', 'Mini-ITX']

data = {
    'Category': [], 'Name': [], 'Price_PLN': [], 'Performance_Score': [],
    'Socket': [], 'RAM_Type': [], 'TDP_W': [], 'Power_W': [],
    'Form_Factor': [], 'Length_mm': [], 'Height_mm': [] 
}

def add_item(category, name, price, perf, socket='', ram_type='', tdp='', power_w='', form_factor='', length_mm='', height_mm=''):
    data['Category'].append(category)
    data['Name'].append(name)
    data['Price_PLN'].append(price)
    data['Performance_Score'].append(perf)
    data['Socket'].append(socket)
    data['RAM_Type'].append(ram_type)
    data['TDP_W'].append(tdp)
    data['Power_W'].append(power_w)
    data['Form_Factor'].append(form_factor)
    data['Length_mm'].append(length_mm)   
    data['Height_mm'].append(height_mm)   

# 1. Procesory
for i in range(2000):
    socket = random.choice(SOCKETS)
    tdp = random.randint(45, 250)
    price = random.randint(300, 3500)
    perf = int(price * random.uniform(0.8, 1.2))
    brand = random.choice(['Intel Core', 'AMD Ryzen'])
    name = f"{brand} Gen-{random.randint(9, 14)} Model-{i}"
    add_item('CPU', name, price, perf, socket=socket, tdp=tdp)

# 2. Chłodzenie CPU 
for i in range(1000):
    max_tdp_cooling = random.choice([65, 130, 200, 250, 300])
    price = int(max_tdp_cooling * random.uniform(1.5, 3.5))
    perf = int(price * random.uniform(0.9, 1.1))
    height = random.randint(120, 170)
    brand = random.choice(['Noctua', 'be quiet!', 'Deepcool', 'Endorfy', 'Arctic'])
    name = f"{brand} Cooler MaxTDP-{max_tdp_cooling}W v{i}"
    add_item('CPU Cooler', name, price, perf, tdp=max_tdp_cooling, height_mm=height)

# 3. Płyty główne
for i in range(1500):
    socket = random.choice(SOCKETS)
    form_factor = random.choice(FORM_FACTORS)
    ram_type = 'DDR5' if socket in ['AM5', 'LGA1851'] else random.choice(RAM_TYPES)
    
    price = random.randint(300, 2000)
    if form_factor == 'Mini-ITX': price += 200 
    perf = int(price * random.uniform(0.8, 1.2))
    
    brand = random.choice(['ASUS', 'MSI', 'Gigabyte', 'ASRock'])
    name = f"{brand} {form_factor}-{socket} v{i}"
    add_item('Motherboard', name, price, perf, socket=socket, ram_type=ram_type, form_factor=form_factor)

# 4. Pamięci RAM
for i in range(2000):
    ram_type = random.choice(RAM_TYPES)
    price = random.randint(150, 1500)
    perf = int(price * random.uniform(0.8, 1.2))
    speed = random.choice([3200, 3600, 4800, 5200, 6000, 7200])
    brand = random.choice(['Corsair', 'Kingston', 'G.Skill', 'Crucial'])
    name = f"{brand} {ram_type} {speed}MHz CL{random.randint(14, 40)}-{i}"
    add_item('RAM', name, price, perf, ram_type=ram_type)

# 5. Karty graficzne 
for i in range(1500):
    tdp = random.randrange(100, 451, 20)
    price = random.randint(800, 8000)
    perf = int(price * random.uniform(0.8, 1.3))
    length = random.randint(200, 280) if price < 2500 else random.randint(280, 360)
    brand = random.choice(['NVIDIA RTX', 'AMD Radeon RX'])
    name = f"{brand} {random.randint(3000, 9000)}-{i}"
    add_item('GPU', name, price, perf, tdp=tdp, length_mm=length)

# 6. Zasilacze
for i in range(1500):
    power_w = random.randrange(300, 1201, 50)
    price = int(power_w * random.uniform(0.5, 1.2))
    perf = int(price * random.uniform(0.9, 1.1))
    brand = random.choice(['Corsair', 'be quiet!', 'Seasonic', 'Endorfy'])
    name = f"{brand} {power_w}W 80+ Gold-{i}"
    add_item('Power Supply', name, price, perf, power_w=power_w)

# 7. Dyski
for i in range(2000):
    price = random.randint(100, 2000)
    perf = int(price * random.uniform(0.8, 1.2))
    brand = random.choice(['Samsung', 'WD', 'Crucial', 'Lexar', 'Kingston'])
    name = f"{brand} NVMe SSD Gen{random.randint(3, 5)}-{i}"
    add_item('Storage', name, price, perf)

# 8. Obudowy 
for i in range(1000):
    form_factor = random.choice(FORM_FACTORS)
    price = random.randint(150, 1000)
    perf = int(price * random.uniform(0.8, 1.2)) 
    

    if form_factor == 'Mini-ITX':
        max_gpu_len = random.randint(200, 280)  
        max_cooler_h = random.randint(120, 145) 
    elif form_factor == 'Micro-ATX':
        max_gpu_len = random.randint(280, 340)
        max_cooler_h = random.randint(145, 160)
    else: 
        max_gpu_len = random.randint(320, 400)
        max_cooler_h = random.randint(160, 180)
        
    brand = random.choice(['Fractal Design', 'NZXT', 'Lian Li', 'Corsair', 'Phanteks'])
    name = f"{brand} {form_factor} Case v{i}"
    add_item('Case', name, price, perf, form_factor=form_factor, length_mm=max_gpu_len, height_mm=max_cooler_h)

df = pd.DataFrame(data)
df.to_csv('dataset.csv', index=False)
