import sqlite3

conn = sqlite3.connect('quesillos.db')
cur = conn.cursor()

tablas = [
    'pedidos',
    
]

for tabla in tablas:
    cur.execute(f'DELETE FROM {tabla}')
    cur.execute(f'DELETE FROM sqlite_sequence WHERE name="{tabla}"')  # Reinicia autoincremental

conn.commit()
conn.close()
