import sqlite3

conn = sqlite3.connect('quesillos.db')
cur = conn.cursor()

tablas = [
<<<<<<< HEAD
    'empleados',
=======
    'pedido_productos',
>>>>>>> 15ab887802db774ea3f854708fdd3260228af0fe
    
]

for tabla in tablas:
    cur.execute(f'DELETE FROM {tabla}')
    cur.execute(f'DELETE FROM sqlite_sequence WHERE name="{tabla}"')  # Reinicia autoincremental

conn.commit()
conn.close()
