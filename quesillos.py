#Script para la creacion de la base de datos en sqlito

import sqlite3
from datetime import datetime

# Conectar a la base de datos SQLite (crea la base de datos si no existe)
conn = sqlite3.connect('quesillos.db')
cursor = conn.cursor()

# Crear las tablas en SQLite
cursor.execute('''
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    telefono TEXT,
    direccion TEXT,
    email TEXT,
    num_mesa INTEGER NOT NULL
);
''')






cursor.executescript('''
BEGIN TRANSACTION;
CREATE TABLE facturas_new (
    codigo INTEGER PRIMARY KEY AUTOINCREMENT,
    monto REAL NOT NULL,
    estado TEXT,
    caja_id INTEGER REFERENCES caja(id),
    propina REAL DEFAULT 0,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO facturas_new(codigo, monto, estado, caja_id, propina)
SELECT codigo, monto, estado, caja_id, propina FROM facturas;
DROP TABLE facturas;
ALTER TABLE facturas_new RENAME TO facturas;
COMMIT;
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    categoria TEXT
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS facturas (
    codigo INTEGER PRIMARY KEY AUTOINCREMENT,
    monto REAL NOT NULL,
    estado TEXT CHECK (estado IN ('pendiente', 'pagada', 'cancelada')),
    caja_id INTEGER,
    FOREIGN KEY (caja_id) REFERENCES caja(id)
);
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS caja (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT DEFAULT (datetime('now')),
    total_facturas INTEGER NOT NULL,
    total_monto REAL NOT NULL,
    tipo_pago TEXT CHECK (tipo_pago IN ('efectivo', 'tarjeta', 'transferencia'))
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora TEXT DEFAULT (datetime('now')),
    tipo_pedido TEXT CHECK (tipo_pedido IN ('domicilio', 'local')),
    clientes_id INTEGER,
    empleado_id INTEGER,
    codigo_factura INTEGER,
    FOREIGN KEY (clientes_id) REFERENCES clientes(id),
    FOREIGN KEY (empleado_id) REFERENCES empleados(id),
    FOREIGN KEY (codigo_factura) REFERENCES facturas(codigo)
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS pedido_productos (
    pedido_id INTEGER,
    producto_id INTEGER,
    cantidad INTEGER NOT NULL,
    PRIMARY KEY (pedido_id, producto_id),
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS entradas_inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_entrada TEXT DEFAULT (datetime('now')),
    cantidad_ingresada INTEGER NOT NULL,
    costo_unitario REAL NOT NULL,
    producto_id INTEGER,
    proveedor TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);
''')



cursor.execute('''
CREATE TABLE IF NOT EXISTS usuario_empleado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_user TEXT,
    contra_user TEXT,
    rol TEXT
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS password_resets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES usuario_empleado(id)
)
''')


# Inserciones iniciales
clientes_data = [
    ('Carlos Pérez', '555-1234', 'Av. Siempre Viva 123', 'carlos@correo.com', 1),
    ('Ana Gómez', '555-5678', 'Calle Falsa 456', 'ana@correo.com', 2),
    # Agregar más datos según sea necesario
]

empleados_data = [
    ('Antonio Martínez', 'Camarero', 1500),
    ('Lucía Sánchez', 'Cocinera', 2000),
    # Agregar más datos según sea necesario
]

productos_data = [
    ('Quesillo de Vaca', 50.00, 'quesillos'),
    ('Quesillo de Cabra', 55.00, 'quesillos'),
    # Agregar más datos según sea necesario
]

facturas_data = [
    (50.00, 'pendiente', 1),
    (70.00, 'pendiente', 2),
    # Agregar más datos según sea necesario
]

caja_data = [
    (5, 250.00, 'efectivo'),
    (8, 400.00, 'tarjeta'),
    # Agregar más datos según sea necesario
]

pedidos_data = [
    ('domicilio', 1, 2, 2),
    ('local', 3, 4, 2),
    # Agregar más datos según sea necesario
]

pedido_productos_data = [
    (4, 7, 1),
    (4, 8, 2),
    # Agregar más datos según sea necesario
]

# Insertar los datos en las tablas
#cursor.executemany('INSERT INTO clientes (nombre, telefono, direccion, email, num_mesa) VALUES (?, ?, ?, ?, ?)', clientes_data)
#cursor.executemany('INSERT INTO empleados (nombre, cargo, salario) VALUES (?, ?, ?)', empleados_data)
#cursor.executemany('INSERT INTO productos (nombre, precio, categoria) VALUES (?, ?, ?)', productos_data)
#cursor.executemany('INSERT INTO facturas (monto, estado, caja_id) VALUES (?, ?, ?)', facturas_data)
#cursor.executemany('INSERT INTO caja (total_facturas, total_monto, tipo_pago) VALUES (?, ?, ?)', caja_data)
#cursor.executemany('INSERT INTO pedidos (tipo_pedido, clientes_id, empleado_id, codigo_factura) VALUES (?, ?, ?, ?)', pedidos_data)
#cursor.executemany('INSERT INTO pedido_productos (pedido_id, producto_id, cantidad) VALUES (?, ?, ?)', pedido_productos_data)
#


try:
    cursor.execute('''UPDATE facturas SET estado = 'pagada' WHERE estado = 'pendiente'
                ''')
except sqlite3.OperationalError as e:
   print(f'Error: {e}')
# Confirmar los cambios y cerrar la conexión
conn.commit()
conn.close()

print("Base de datos y tablas creadas exitosamente, y datos insertados.")


