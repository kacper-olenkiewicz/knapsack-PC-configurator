import pandas as pd
import random

SOCKETS = ['AM4', 'AM5', 'LGA1200', 'LGA1700', 'LGA1851']
RAM_TYPES = ['DDR4', 'DDR5']

data = {
    'Category': [], 'Name': [], 'Price_PLN': [], 'Performance_Score': [],
    'Socket': [], 'RAM_Type': [], 'TDP_W': [], 'Power_W': []
}

def add_item(category, name, price, perf, socket='', ram_type='', tdp='', power_w=''):
    data['Category'].append(category)
    data['Name'].append(name)
    data['Price_PLN'].append(price)
    data['Performance_Score'].append(perf)
    data['Socket'].append(socket)
    data['RAM_Type'].append(ram_type)
    data['TDP_W'].append(tdp)
    data['Power_W'].append(power_w)

#procesory
for i in range(2000):
    socket = random.choice(SOCKETS)
    tdp = random.randint(5, 100)
    price = random.randint(300, 3500)
    perf = random.randint(10, 100)
    brand = random.choice(['Intel Core', 'AMD Ryzen'])
    name = f"{brand} Gen-{random.randint(9, 14)} Model-{i}"
    add_item('CPU', name, price, perf, socket=socket, tdp=tdp)

#plyty glowne
for i in range(1500):
    socket = random.choice(SOCKETS)
    ram_type = random.choice(RAM_TYPES)
    # Drobna poprawka dla realizmu - najnowsze sockety wymuszają DDR5
    if socket in ['AM5', 'LGA1851']:
        ram_type = 'DDR5'
        
    price = random.randint(300, 2000)
    perf = random.randint(10, 100)
    brand = random.choice(['ASUS', 'MSI', 'Gigabyte', 'ASRock'])
    name = f"{brand} PRO-{socket} v{i}"
    add_item('Motherboard', name, price, perf, socket=socket, ram_type=ram_type)

#pamieci ram
for i in range(2000):
    ram_type = random.choice(RAM_TYPES)
    price = random.randint(150, 1500)
    perf = random.randint(10, 100)
    speed = random.choice([3200, 3600, 4800, 5200, 6000, 7200])
    brand = random.choice(['Corsair', 'Kingston', 'G.Skill', 'Crucial'])
    name = f"{brand} {ram_type} {speed}MHz CL{random.randint(14, 40)}-{i}"
    add_item('RAM', name, price, perf, ram_type=ram_type)

#karty graficzne
for i in range(1500):
    tdp = random.randrange(100, 701, 20)
    price = random.randint(800, 8000)
    perf = random.randint(10, 100)
    brand = random.choice(['NVIDIA RTX', 'AMD Radeon RX'])
    name = f"{brand} {random.randint(3000, 9000)}-{i}"
    add_item('GPU', name, price, perf, tdp=tdp)

#zasilacze
for i in range(1500):
    power_w = random.randrange(300, 1001, 50)
    price = random.randint(150, 1200)
    perf = random.randint(10, 100)
    brand = random.choice(['Corsair', 'be quiet!', 'Seasonic', 'Endorfy'])
    name = f"{brand} {power_w}W 80+ Gold-{i}"
    add_item('Power Supply', name, price, perf, power_w=power_w)

#dyski
for i in range(2000):
    price = random.randint(100, 2000)
    perf = random.randint(10, 100)
    brand = random.choice(['Samsung', 'WD', 'Crucial', 'Lexar', 'Kingston'])
    name = f"{brand} NVMe SSD Gen{random.randint(3, 5)}-{i}"
    add_item('Storage', name, price, perf)


df = pd.DataFrame(data)
df.to_csv('dataset.csv', index=False)
print("Dataset generated and saved to 'dataset.csv'")