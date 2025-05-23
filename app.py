from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_session import Session
from functools import wraps
import sqlite3
import secrets
from datetime import datetime, timedelta
from flask import make_response
from dotenv import load_dotenv
import random
import os
from flask import Flask
from flask_mail import Mail, Message
import pandas as pd
import io
from flask import send_file
import shutil
from pathlib import Path
import threading
import schedule
import time


# Cargar variables de entorno
load_dotenv()

# Configuración del directorio de respaldos
BACKUP_DIR = Path('backups')
BACKUP_DIR.mkdir(exist_ok=True)

def create_backup():
    """
    Crea una copia de seguridad de la base de datos
    """
    try:
        # Obtener la fecha y hora actual
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Nombre del archivo de respaldo
        backup_filename = f'quesillos_backup_{timestamp}.db'
        backup_path = BACKUP_DIR / backup_filename
        
        # Crear la copia de seguridad
        shutil.copy2('quesillos.db', backup_path)
        
        # Mantener solo las últimas 10 copias de seguridad
        backups = sorted(BACKUP_DIR.glob('quesillos_backup_*.db'))
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                old_backup.unlink()
        
        print(f'Copia de seguridad creada exitosamente: {backup_filename}')
        return True
        
    except Exception as e:
        print(f'Error al crear la copia de seguridad: {str(e)}')
        return False

def run_scheduler():
    """
    Ejecuta el programador de copias de seguridad en segundo plano
    """
    schedule.every(8).hours.do(create_backup)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Iniciar el programador en un hilo separado
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

app = Flask(__name__)

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get("user_id") is None:
                return redirect("/login")
            
            cursor = connection.cursor()
            cursor.execute("SELECT rol FROM usuario_empleado WHERE id = ?", (session.get("user_id"),))
            user = cursor.fetchone()
            
            if not user or user['rol'] not in roles:
                flash("No tienes permiso para acceder a esta página", "error")
                return redirect(url_for('mesas1'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.template_filter()   # toma el nombre 'number_format'
def number_format(value, decimals=0):
    try:
        val = float(value)
    except (TypeError, ValueError):
        return "0"
    txt = f"{val:,.{decimals}f}"
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")

@app.template_filter('datetimeformat')
def datetimeformat(value):
    if value:
        return value.strftime('%d/%m/%Y %H:%M')
    return ''

app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave segura en producción

# Configuración de sesión
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuración de la base de datos
database_path = "quesillos.db"
connection = sqlite3.connect(database_path, check_same_thread=False)
connection.row_factory = sqlite3.Row

# Configurar la zona horaria de Nicaragua (UTC-6)
connection.execute("PRAGMA timezone = '-06:00'")

# Asegurar que la tabla pedidos tenga la columna estado
try:
    connection.execute("ALTER TABLE pedidos ADD COLUMN estado TEXT DEFAULT 'pendiente'")
    connection.commit()
except sqlite3.OperationalError:
    # La columna ya existe, no hacer nada
    pass

def get_db():
    """Retorna la conexión a la base de datos existente"""
    return connection

#implementacion temporal para el estado de las mesas
mesas = [
    {'id': 1, 'nombre': 'MESA 1', 'atendida': False},
    {'id': 2, 'nombre': 'MESA 2', 'atendida': False},
    {'id': 3, 'nombre': 'MESA 3', 'atendida': False},
    {'id': 4, 'nombre': 'MESA 4', 'atendida': False},
    {'id': 5, 'nombre': 'MESA 5', 'atendida': False},
    {'id': 6, 'nombre': 'MESA 6', 'atendida': False},
    {'id': 7, 'nombre': 'MESA 7', 'atendida': False},
    {'id': 8, 'nombre': 'MESA 8', 'atendida': False},
    {'id': 9, 'nombre': 'MESA 9', 'atendida': False},
    {'id': 10, 'nombre': 'MESA 10', 'atendida': False},
    {'id': 11, 'nombre': 'MESA 11', 'atendida': False},
    {'id': 12, 'nombre': 'MESA 12', 'atendida': False},
    {'id': 13, 'nombre': 'MESA 13', 'atendida': False},
    {'id': 14, 'nombre': 'PARA LLEVAR', 'imagen': 'delivery.svg'},
    {'id': 15, 'nombre': 'BARRA', 'imagen': 'barra.webp'}
]





# Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

# Variable global para almacenar OTP
stored_otp = None

def generate_otp():
    """Genera un código OTP de 6 dígitos"""
    return str(random.randint(100000, 999999))

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

def send_otp(email, otp):
    msg = Message('Tu código OTP',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email])

    # Correo HTML bonito
    msg.html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; border-radius: 10px; box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.1);">
            <h2 style="color: #007bff; text-align: center;">Recuperación de Contraseña</h2>
            <p style="font-size: 16px; line-height: 1.6;">Hola,</p>
            <p style="font-size: 16px; line-height: 1.6;">Se ha solicitado un código de recuperación de contraseña para tu cuenta.</p>
            <h3 style="color: #ff5733; text-align: center;">Tu código OTP es: <strong>{otp}</strong></h3>
            <p style="font-size: 16px; line-height: 1.6;">Este código es válido por 10 minutos. Si no solicitaste este cambio, por favor ignora este mensaje.</p>
            <div style="text-align: center; margin-top: 20px;">
                <p style="font-size: 14px;">Si tienes problemas con este correo, por favor contacta a nuestro soporte.</p>
                <p style="font-size: 14px; color: #007bff;">Soporte técnico</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Enviar el correo
    try:
        mail.send(msg)
        print(f"OTP enviado a {email}")
    except Exception as e:
        print(f"Error al enviar OTP: {e}")

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    global stored_otp  # Usar la variable global

    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        try:
            # Conectar a la base de datos
            db = get_db()  # Asegúrate de tener esta función 'get_db' que te devuelva la conexión
            cursor = db.cursor()

            # Consultar si el correo existe en la tabla usuario_empleado
            cursor.execute("SELECT id FROM usuario_empleado WHERE email = ?", (email,))
            user = cursor.fetchone()

            if not user:
                flash('El correo electrónico no está registrado en nuestra base de datos.', 'danger')
                return redirect(url_for('forgot_password'))

            # Generar OTP
            stored_otp = generate_otp()

            # Enviar OTP por correo
            send_otp(email, stored_otp)

            flash('Te hemos enviado un código OTP a tu correo.', 'info')
            return redirect(url_for('verify_otp', email=email))  # Pasa el email como parámetr

        except sqlite3.Error as e:
            print(f"[ERROR SQLite] {e}")
            flash('Hubo un error con la base de datos. Intenta nuevamente más tarde.', 'danger')
            return redirect(url_for('forgot_password'))

    return render_template('pass.html')

from flask import render_template
import sqlite3

# Crear la tabla si no existe
with app.app_context():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            tipo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            precio DECIMAL(10,2) NOT NULL
        )
    """)
    db.commit()
@app.route('/historial')
@login_required
@role_required(['admin']) 
def historial():
    try:
        cursor = connection.cursor()

        # Propinas de hoy
        cursor.execute("""
            SELECT IFNULL(SUM(f.propina), 0) as total
            FROM facturas f
            JOIN pedidos p ON f.codigo = p.codigo_factura
            WHERE date(p.fecha_hora, 'localtime') = date('now', 'localtime')
        """)
        propinas_hoy = cursor.fetchone()['total']

        # Propinas de este mes
        cursor.execute("""
            SELECT IFNULL(SUM(f.propina), 0) as total
            FROM facturas f
            JOIN pedidos p ON f.codigo = p.codigo_factura
            WHERE strftime('%Y-%m', p.fecha_hora, 'localtime') = strftime('%Y-%m', 'now', 'localtime')
        """)
        propinas_mes = cursor.fetchone()['total']

        # Ventas de hoy 
        cursor.execute("""
            SELECT SUM(f.monto) as total 
            FROM facturas f
            JOIN pedidos p ON f.codigo = p.codigo_factura
            WHERE date(p.fecha_hora, 'localtime') = date('now', 'localtime')
            AND f.estado = 'pagada';
        """)
        ventas_dia = cursor.fetchone()[0] or 0

        # Órdenes de hoy
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pedidos p
            JOIN facturas f ON p.codigo_factura = f.codigo
            WHERE date(p.fecha_hora, 'localtime') = date('now', 'localtime')
            AND f.estado = 'pagada'
        """)
        ordenes_dia = cursor.fetchone()[0] or 0

        # Clientes únicos hoy
        cursor.execute("""
            SELECT COUNT(DISTINCT c.id) 
            FROM pedidos p
            JOIN clientes c ON p.clientes_id = c.id
            WHERE date(p.fecha_hora, 'localtime') = date('now', 'localtime')
        """)
        clientes_dia = cursor.fetchone()[0] or 0

        # Ventas mensuales
        cursor.execute("""
            SELECT strftime('%m', p.fecha_hora, 'localtime') as mes, SUM(f.monto) as total
            FROM facturas f
            JOIN pedidos p ON f.codigo = p.codigo_factura
            WHERE f.estado = 'pagada'
            GROUP BY mes
            ORDER BY mes
        """)
        ventas_mensuales = [0] * 12
        for row in cursor.fetchall():
            mes = int(row[0]) - 1
            ventas_mensuales[mes] = row[1] or 0

        # Ventas totales
        cursor.execute("""
            SELECT SUM(f.monto)
            FROM facturas f
            JOIN pedidos p ON f.codigo = p.codigo_factura
            WHERE f.estado = 'pagada'
        """)
        ventas_totales = cursor.fetchone()[0] or 0

        # Productos más vendidos
        cursor.execute("""
            SELECT pr.nombre, SUM(pp.cantidad) as ventas
            FROM pedido_productos pp
            JOIN productos pr ON pp.producto_id = pr.id
            GROUP BY pr.nombre
            ORDER BY ventas DESC
            LIMIT 5
        """)
        productos_mas_vendidos = cursor.fetchall() or []

        # Mesas más usadas
        cursor.execute("""
            SELECT cl.nombre as mesa, COUNT(*) as uso
            FROM pedidos p
            JOIN clientes cl ON p.clientes_id = cl.id
            WHERE cl.nombre != 'Cliente Barra'
            GROUP BY cl.nombre
            ORDER BY uso DESC
            LIMIT 5
        """)
        mesas_mas_usadas = cursor.fetchall() or []

        # Gastos mensuales
        cursor.execute("""
            SELECT strftime('%m', fecha) as mes, SUM(precio) as total
            FROM movimientos_caja
            WHERE tipo = 'salida'
            GROUP BY mes
            ORDER BY mes
        """)
        gastos_mensuales = [0] * 12
        for row in cursor.fetchall():
            mes = int(row[0]) - 1
            gastos_mensuales[mes] = row[1] or 0

        # Mejores meses (top 5)
        cursor.execute("""
            SELECT strftime('%m', p.fecha_hora, 'localtime') as mes, SUM(f.monto) as total
            FROM facturas f
            JOIN pedidos p ON f.codigo = p.codigo_factura
            WHERE f.estado = 'pagada'
            GROUP BY mes
            ORDER BY total DESC
            LIMIT 5
        """)
        top_months = cursor.fetchall() or []
        meses_top = [f"Mes {row[0]}" for row in top_months]
        ventas_top = [row[1] or 0 for row in top_months]

        return render_template("historial.html",
                            ventas_dia=ventas_dia,
                            ordenes_dia=ordenes_dia,
                            clientes_dia=clientes_dia,
                            ventas_mensuales=ventas_mensuales,
                            ventas_totales=ventas_totales,
                            productos_mas_vendidos=productos_mas_vendidos,
                            mesas_mas_usadas=mesas_mas_usadas,
                            gastos_mensuales=gastos_mensuales,
                            meses_top=meses_top,
                            ventas_top=ventas_top,
                            propinas_hoy=propinas_hoy,
                            propinas_mes=propinas_mes)
    except Exception as e:
        print(f"Error en historial: {e}")
        return "Error al obtener datos históricos", 500
        
@app.route('/exportar_todas_metricas')
@login_required
@role_required(['admin'])  # Solo administradores pueden acceder
def exportar_todas_metricas():
    conn = sqlite3.connect('quesillos.db')

    # Métricas individuales
    propinas_hoy = pd.read_sql_query("""
        SELECT IFNULL(SUM(propina), 0) AS total 
        FROM facturas 
        WHERE DATE(fecha_creacion) = DATE('now')
    """, conn).iloc[0, 0]

    propinas_semana = pd.read_sql_query("""
        SELECT IFNULL(SUM(propina), 0) AS total 
        FROM facturas 
        WHERE strftime('%W', fecha_creacion) = strftime('%W', 'now')
          AND strftime('%Y', fecha_creacion) = strftime('%Y', 'now')
    """, conn).iloc[0, 0]

    propinas_mes = pd.read_sql_query("""
        SELECT IFNULL(SUM(propina), 0) AS total 
        FROM facturas 
        WHERE strftime('%Y-%m', fecha_creacion) = strftime('%Y-%m', 'now')
    """, conn).iloc[0, 0]

    # DataFrame resumen
    resumen_df = pd.DataFrame({
        'Métrica': ['Propinas Hoy', 'Propinas Semana', 'Propinas Mes'],
        'Monto (C$)': [propinas_hoy, propinas_semana, propinas_mes]
    })

    # Detalle por día
    detalle_df = pd.read_sql_query("""
        SELECT DATE(fecha_creacion) AS Fecha, 
               SUM(propina) AS 'Propinas Diarias'
        FROM facturas
        GROUP BY DATE(fecha_creacion)
        ORDER BY Fecha DESC
    """, conn)

    conn.close()

    # Crear Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        resumen_df.to_excel(writer, index=False, sheet_name='Resumen')
        detalle_df.to_excel(writer, index=False, sheet_name='Detalle Diario')
    output.seek(0)

    return send_file(output, as_attachment=True,
                     download_name='metricas_propinas.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    global stored_otp
    if request.method == 'POST':
        otp_input = request.form['otp']
        email = request.form.get('email')  # Asegúrate de pasar el email desde el formulario

        if otp_input == stored_otp:
            try:
                # Buscar al usuario en la base de datos
                cursor = connection.cursor()
                cursor.execute("SELECT id, nombre_user, rol FROM usuario_empleado WHERE email = ?", (email,))
                user = cursor.fetchone()
                
                if user:
                    flash("OTP verificado correctamente. Por favor, establece tu nueva contraseña.", "success")
                    return redirect(url_for('change_password', email=email))
                else:
                    flash("Usuario no encontrado.", "error")
                    return redirect(url_for('login'))
            
            except sqlite3.Error as e:
                print(f"[ERROR SQLite] {e}")
                flash("Error al verificar el usuario.", "error")
                return redirect(url_for('login'))
        else:
            flash("Código OTP incorrecto. Intenta nuevamente.", "error")
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    email = request.args.get('email')
    if not email:
        flash("Error: No se proporcionó el correo electrónico.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')

        if new_password != confirm_password:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for('change_password', email=email))

        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE usuario_empleado 
                SET contra_user = ? 
                WHERE email = ?
            """, (new_password, email))
            connection.commit()
            
            flash("Contraseña actualizada exitosamente. Por favor, inicia sesión con tu nueva contraseña.", "success")
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            print(f"[ERROR SQLite] {e}")
            flash("Error al actualizar la contraseña.", "error")
            return redirect(url_for('change_password', email=email))

    return render_template('change_password.html', email=email)

# Ruta para la página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            return redirect(url_for('login', error='empty'))

        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT * FROM usuario_empleado WHERE nombre_user = ? AND contra_user = ?
            """, (username, password))
            user = cursor.fetchone()
            
            if not user:
                return redirect(url_for('login', error='invalid'))

            session['user_id'] = user[0]
            session['username'] = username
            session['rol'] = user['rol']
            print("Sesión iniciada correctamente")
            print("User ID guardado en la sesión:", session.get('user_id'))
            print("Rol guardado en la sesión:", session.get('rol'))

            # Redirigir según el rol
            if user['rol'] == 'admin':
                return redirect(url_for('admin_pedidos_en_curso'))
            return redirect(url_for('mesas1'))
        except Exception as e:
            print(f"Error en la consulta: {e}")
            return redirect(url_for('login', error='server'))
    
    return render_template('login.html')



#cierre de sesion
@app.route("/logout", methods=['GET', 'POST'])
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")

# Ruta para la página principal
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # Obtener el rol del usuario actual
    cursor = connection.cursor()
    cursor.execute("SELECT rol FROM usuario_empleado WHERE id = ?", (session.get("user_id"),))
    user = cursor.fetchone()
    
    if user and user['rol'] == 'admin':
        return redirect(url_for('admin_pedidos_en_curso'))
    return redirect(url_for('mesas1'))




    
    
#ruta para el renderizado del login
@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])  # Solo administradores pueden acceder
def usuarios():
    if request.method == 'POST':
        user = request.form['usuario']
        contra = request.form['password']
        rol = request.form.get('rol', 'mesero')  # Por defecto es mesero
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO usuario_empleado (nombre_user, contra_user, rol) VALUES (?, ?, ?)
            """, (user, contra, rol))
            connection.commit()
            flash("Usuario creado correctamente")
            return redirect(url_for('usuarios'))
        except:
            flash("No se pudo crear el usuario")
    else:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT * FROM usuario_empleado
                WHERE nombre_user IS NOT NULL
                AND nombre_user != ''
            """)
            table = cursor.fetchall()
        except:
            print("Error no se pudieron extraer los datos de la base de datos")
        return render_template("usuarios.html", info=table)
    
#ruta para el ingreso de productos
@app.route('/ingresoproducto', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'mesero'])  # Permitir acceso a admin y mesero
def ingresoproducto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = float(request.form['precio'])
        categoria = request.form.get('categoria')
        print(categoria)
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO productos (nombre, precio, categoria, stock) VALUES (?, ?, ?, 0)
            """, (nombre, precio, categoria))
            flash("Producto Ingresado Correctamente")
            connection.commit()
            return redirect(url_for('catalogoproductos'))
            
        except:
            flash("No se pudo ingresar el producto")

    else:
        return render_template("registroproducto.html")
    
#Ruta en la que podemos ver todo el listado de platillos y bebidas
@app.route('/catalogoproductos', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'mesero'])  # Permitir acceso a admin y mesero
def catalogoproductos():
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM productos
        """)
        table = cursor.fetchall()
    except:
        print("Error no se pudieron extraer los datos de la base de datos")
    return render_template("catalogoproductos.html", info=table)






#Ruta en la que podemos ver todo el listado de platillos y bebidas
@app.route('/entradaproducto', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'mesero', 'cocinero'])  # Permitir acceso a admin, mesero y cocinero
def entradaproductos():
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM productos
        """)
        table = cursor.fetchall()
    except:
        print("Error no se pudieron extraer los datos de la base de datos")
    return render_template("entryproducts.html", info=table)

@app.route('/registrar_pedido', methods=['POST'])
@login_required
def registrar_pedido():
    try:
        proveedor = request.form['proveedor']
        cantidad = int(request.form['cantidad'])  # Aseguramos que sea número
        costo = request.form['costo']
        fecha = request.form['fecha']
        producto_id = request.form['producto_id']
        
        cursor = connection.cursor()
        
        # Insertar en entradas_inventario
        cursor.execute("""
            INSERT INTO entradas_inventario 
            (proveedor, fecha_entrada, cantidad_ingresada, costo_unitario, producto_id)
            VALUES (?, ?, ?, ?, ?)
        """, (proveedor, fecha, cantidad, costo, producto_id))

        # Actualizar el stock en productos
        cursor.execute("""
            UPDATE productos
            SET stock = stock + ?
            WHERE id = ?
        """, (cantidad, producto_id))

        connection.commit()
        flash('Entrada registrada correctamente.', 'success')
    except Exception as e:
        print("Error al registrar el pedido:", e)
        flash('Hubo un error al registrar el pedido.', 'danger')
    
    return redirect(url_for('registro'))


@app.route('/registrar_producto_ajax', methods=['POST'])
@login_required
def registrar_producto_ajax():
    try:
        data = request.json
        proveedor = data['proveedor']
        producto_id = data['producto_id']
        cantidad = int(data['cantidad'])  # Aseguramos que sea número
        costo = data['costo']
        fecha = data['fecha']

        cursor = connection.cursor()

        # Insertar en entradas_inventario
        cursor.execute("""
            INSERT INTO entradas_inventario 
            (proveedor, fecha_entrada, cantidad_ingresada, costo_unitario, producto_id)
            VALUES (?, ?, ?, ?, ?)
        """, (proveedor, fecha, cantidad, costo, producto_id))

        # Actualizar el stock en productos
        cursor.execute("""
            UPDATE productos
            SET stock = stock + ?
            WHERE id = ?
        """, (cantidad, producto_id))

        connection.commit()

        return jsonify({
            'status': 'success',
            'message': 'Entrada registrada correctamente'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500



#mostrar clientes
@app.route('/clientes', methods = ['GET', 'POST'])
@login_required
def clientes ():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * from clientes
    """)
    table = cursor.fetchall()
    
        
    return render_template("clientes.html", info=table)

@app.route('/clientes/editar/<int:id>', methods=['POST'])
@login_required
def editar_cliente(id):
    nombre = request.form['nombre']
    telefono = request.form['telefono']
    direccion = request.form['direccion']
    email = request.form['email']
    
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE clientes
        SET nombre = ?, telefono = ?, direccion = ?, email = ?
        WHERE id = ?
    """, (nombre, telefono, direccion, email, id))
    connection.commit()
    cursor.close()
    
    flash("Cliente actualizado exitosamente")
    return redirect(url_for('clientes'))


#solicitudes fetch para actualizar el valor de los productos
@app.route('/productos/editar/<int:id>', methods=['POST'])
@login_required
@role_required(['admin'])  # Solo administradores pueden acceder
def editar_producto(id):
    nombre = request.form['nombre']
    precio = request.form['precio']
    stock = request.form.get('stock')
    
    cursor = connection.cursor()
    if stock is not None:
        cursor.execute("""
            UPDATE productos
            SET nombre = ?, precio = ?, stock = ?
            WHERE id = ?
        """, (nombre, precio, stock, id))
    else:
        cursor.execute("""
            UPDATE productos
            SET nombre = ?, precio = ?
            WHERE id = ?
        """, (nombre, precio, id))
    connection.commit()
    cursor.close()
    
    flash("Producto actualizado exitosamente")
    return redirect(url_for('catalogoproductos'))

@app.route('/clientes/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_cliente(id):
    # Conexión a la base de datos
    cursor = connection.cursor()

    # Ejecutar la consulta para eliminar el cliente
    cursor.execute("""
        DELETE FROM clientes
        WHERE id = ?
    """, (id,))
    
    connection.commit()

    cursor.close()

    # Mostrar mensaje de éxito
    flash("Cliente eliminado exitosamente", "success")
    
    # Retornar una respuesta en JSON para manejar la eliminación en el frontend
    return jsonify({"status": "success"})


#ruta para realizar los pedidos
@app.route('/products', methods=['GET', 'POST'])
@login_required
@role_required(['mesero']) # Restringir a meseros para ordenar
def products():
    mesa_id = request.args.get('mesa_id')
    
    # Validar mesa_id
    if not mesa_id or not mesa_id.isdigit() or int(mesa_id) < 1 or int(mesa_id) > len(mesas):
        flash('Mesa no válida', 'error')
        return redirect(url_for('mesas1'))
        
    mesa_id = int(mesa_id)
    mesa_nombre = mesas[mesa_id - 1]['nombre']
    
    # Obtener lista de meseros
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT DISTINCT id, nombre_user, rol 
            FROM usuario_empleado 
            WHERE rol = 'mesero'
            AND nombre_user IS NOT NULL
            AND nombre_user != ''
        """)
        meseros = cursor.fetchall()
    except Exception as e:
        print(f"Error obteniendo meseros: {e}")
        meseros = []
    
    # Usar hora local de Nicaragua
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('pedidos.html', 
                         mesa_id=mesa_id, 
                         fecha=fecha, 
                         mesa_nombre=mesa_nombre,
                         meseros=meseros)

#ruta para el renderizado de la plantilla de mesas
@app.route('/mesas', methods=['GET', 'POST'])
@login_required
def mesas1():
    return render_template("mesas.html", mesas = mesas)


#ruta de prueba para el menu principal
@app.route('/test', methods=['GET', 'POST'])
@login_required
def testi():
    return render_template("test.html")

# Ruta para obtener productos de una categoría específica
@app.route('/products/<categoryName>')
@login_required
def get_products(categoryName):
    cursor = connection.cursor()
    query = "SELECT id, nombre, precio, stock FROM productos WHERE categoria = ?"  # Agregamos stock a la consulta
    cursor.execute(query, (categoryName,))
    products = cursor.fetchall()
    print(f"Category ID: {categoryName}")
    print(f"Products found: {len(products)}")
    print(products)
    
    # Convertimos los resultados en una lista de diccionarios
    product_list = [{"id": row[0], "nombre": row[1], "precio": row[2], "stock": row[3]} for row in products]
    print(product_list)
    return jsonify(product_list)

# Lista global para almacenar las notificaciones
notificaciones_pedidos = []

@app.route('/notificaciones')
@login_required
@role_required(['admin', 'mesero'])  # Permitir acceso a admin y meseros
def obtener_notificaciones():
    # Obtener solo las notificaciones no leídas
    notificaciones_no_leidas = [n for n in notificaciones_pedidos if not n.get('leida', False)]
    return jsonify(notificaciones_no_leidas)

@app.route('/marcar_notificacion_leida/<int:notificacion_id>', methods=['POST'])
@login_required
@role_required(['admin', 'mesero', 'cocinero'])
def marcar_notificacion_leida(notificacion_id):
    try:
        # Buscar la notificación por ID
        notificacion_encontrada = False
        for notif in notificaciones_pedidos:
            if notif['id'] == notificacion_id:
                notif['leida'] = True
                notificacion_encontrada = True
                break
        
        if not notificacion_encontrada:
            return jsonify({'error': 'Notificación no encontrada'}), 404
            
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error al marcar notificación como leída: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/atender_mesa/<int:mesa_id>', methods=['POST'])
@login_required
@role_required(['mesero']) # Restringir a meseros para atender mesas
def atender_mesa(mesa_id):
    try:
        data = request.get_json()
        order_data = data.get('orderData', [])
        cliente = data.get('cliente', '')
        mesero_id = data.get('mesero_id')  # Nuevo campo para el mesero
        
        if not order_data:
            return jsonify({'error': 'No hay productos en el pedido'}), 400
            
        if not mesero_id:
            return jsonify({'error': 'Debe seleccionar un mesero'}), 400

        cursor = connection.cursor()
        
        # Agrupar productos por ID y sumar cantidades
        productos_agrupados = {}
        for item in order_data:
            producto_id = item['id']
            if producto_id in productos_agrupados:
                productos_agrupados[producto_id]['cantidad'] += item['cantidad']
            else:
                productos_agrupados[producto_id] = {
                    'cantidad': item['cantidad'],
                    'precio': item['precio'],
                    'nombre': item['nombre']
                }

        # Verificar stock para cada producto agrupado
        for producto_id, datos in productos_agrupados.items():
            cursor.execute("SELECT stock FROM productos WHERE id = ?", (producto_id,))
            result = cursor.fetchone()
            if not result or result['stock'] < datos['cantidad']:
                return jsonify({'error': f'Stock insuficiente para el producto {datos["nombre"]}'}), 400

        # Obtener nuevo código de factura
        cursor.execute("SELECT COALESCE(MAX(codigo), 0) FROM facturas")
        last_code = cursor.fetchone()[0]
        new_code = last_code + 1

        # Calcular monto total usando los productos agrupados
        monto_total = sum(datos['precio'] * datos['cantidad'] for datos in productos_agrupados.values())

        try:
            # Iniciar transacción
            cursor.execute("BEGIN TRANSACTION")

            # Insertar factura
            cursor.execute("""
                INSERT INTO facturas (codigo, monto, estado, fecha_creacion)
                VALUES (?, ?, 'pendiente', datetime('now', 'localtime'))
            """, (new_code, monto_total))

            # Insertar cliente
            cursor.execute("""
                INSERT INTO clientes (nombre, num_mesa)
                VALUES (?, ?)
            """, (cliente or 'Cliente General', mesa_id))
            cliente_id = cursor.lastrowid

            # Insertar pedido con el mesero seleccionado
            cursor.execute("""
                INSERT INTO pedidos (fecha_hora, tipo_pedido, clientes_id, empleado_id, codigo_factura)
                VALUES (datetime('now', 'localtime'), 'local', ?, ?, ?)
            """, (cliente_id, mesero_id, new_code))
            pedido_id = cursor.lastrowid

            # Insertar productos del pedido (usando los productos agrupados)
            for producto_id, datos in productos_agrupados.items():
                # Verificar si ya existe el producto en el pedido
                cursor.execute("""
                    SELECT cantidad FROM pedido_productos 
                    WHERE pedido_id = ? AND producto_id = ?
                """, (pedido_id, producto_id))
                existing = cursor.fetchone()

                if existing:
                    # Si existe, actualizar la cantidad
                    nueva_cantidad = existing['cantidad'] + datos['cantidad']
                    cursor.execute("""
                        UPDATE pedido_productos 
                        SET cantidad = ? 
                        WHERE pedido_id = ? AND producto_id = ?
                    """, (nueva_cantidad, pedido_id, producto_id))
                else:
                    # Si no existe, insertar nuevo
                    cursor.execute("""
                        INSERT INTO pedido_productos (pedido_id, producto_id, cantidad)
                        VALUES (?, ?, ?)
                    """, (pedido_id, producto_id, datos['cantidad']))
                
                # Actualizar stock
                cursor.execute("""
                    UPDATE productos 
                    SET stock = stock - ? 
                    WHERE id = ?
                """, (datos['cantidad'], producto_id))

            # Actualizar estado de la mesa
            for mesa in mesas:
                if mesa['id'] == mesa_id:
                    mesa['atendida'] = True
                    break

            # Crear notificación
            hora_actual = datetime.now().strftime('%H:%M')
            notificacion = {
                'id': len(notificaciones_pedidos) + 1,
                'tipo': 'nuevo_pedido',
                'mensaje': f'Pedido #{new_code} - Mesa {mesa_id}',
                'fecha': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'mesa_id': mesa_id,
                'factura_id': pedido_id,
                'leida': False,
                'detalles': {
                    'cliente': cliente or 'Cliente General',
                    'hora': hora_actual,
                    'total_productos': len(productos_agrupados),
                    'total_monto': monto_total,
                    'productos': [{'nombre': datos['nombre'], 'cantidad': datos['cantidad']} 
                                for datos in productos_agrupados.values()]
                }
            }
            notificaciones_pedidos.append(notificacion)

            # Confirmar transacción
            cursor.execute("COMMIT")

            return jsonify({
                'success': True,
                'redirect': url_for('mesas1'),
                'notificacion': notificacion
            })

        except Exception as e:
            # Si hay error, revertir transacción
            cursor.execute("ROLLBACK")
            raise e

    except Exception as e:
        print(f"Error al procesar el pedido: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/finalizar/<int:mesa_id>', methods=['GET', 'POST'])
@login_required
def finalizar(mesa_id):
    global notificaciones_pedidos
    cursor = connection.cursor()
    if request.method == 'POST':
        try:
            pedido_id = request.args.get('pedido_id')
            if not pedido_id:
                cursor.execute('''SELECT 
                    pedidos.id AS id
                    FROM clientes
                    JOIN pedidos ON clientes.id = pedidos.clientes_id
                    JOIN pedido_productos ON pedidos.id = pedido_productos.pedido_id
                    JOIN productos ON pedido_productos.producto_id = productos.id
                    JOIN facturas ON pedidos.codigo_factura = facturas.codigo
                    WHERE clientes.num_mesa = ? AND facturas.estado = 'pendiente';''', (mesa_id,))
            
                pedido_id = cursor.fetchone()
                pedido_id = pedido_id['id']

            incluir_propina = request.form.get('propina')  
            tipo_pago = request.form.get('tipo_pago')
            tipo_tarjeta = request.form.get('tipo_tarjeta') if tipo_pago == 'tarjeta' else None

            cursor.execute('SELECT monto FROM facturas WHERE codigo = (SELECT codigo_factura FROM pedidos WHERE pedidos.id = ?)', (pedido_id,))
            factura = cursor.fetchone()
            total_factura = factura[0]
            propina = total_factura * 0.10 if incluir_propina else 0
            nuevo_total = total_factura + propina
            
            # Actualizar factura
            cursor.execute('''UPDATE facturas 
                          SET estado = 'pagada', 
                              monto = ?,
                              propina = ?,
                              tipo_pago = ?,
                              tipo_tarjeta = ?
                          WHERE codigo = (SELECT codigo_factura FROM pedidos WHERE pedidos.id = ?)''', 
                          (nuevo_total, propina, tipo_pago, tipo_tarjeta, pedido_id))

            # Actualizar estado del pedido
            cursor.execute('''UPDATE pedidos 
                          SET estado = 'completado'
                          WHERE id = ?''', (pedido_id,))

            # Obtener información detallada del pedido para la notificación
            cursor.execute('''
                SELECT 
                    f.codigo,
                    cl.num_mesa,
                    cl.nombre as cliente_nombre,
                    (SELECT GROUP_CONCAT(pr.nombre || ' x' || pp.cantidad)
                     FROM pedido_productos pp
                     JOIN productos pr ON pp.producto_id = pr.id
                     WHERE pp.pedido_id = p.id) as productos,
                    (SELECT SUM(pr.precio * pp.cantidad)
                     FROM pedido_productos pp
                     JOIN productos pr ON pp.producto_id = pr.id
                     WHERE pp.pedido_id = p.id) as total_monto,
                    (SELECT COUNT(*)
                     FROM pedido_productos
                     WHERE pedido_id = p.id) as total_productos
                FROM pedidos p
                JOIN facturas f ON p.codigo_factura = f.codigo
                JOIN clientes cl ON p.clientes_id = cl.id
                WHERE p.id = ?
            ''', (pedido_id,))
            pedido_info = cursor.fetchone()

            if pedido_info:
                factura_codigo = pedido_info['codigo']
                num_mesa = pedido_info['num_mesa']
                mesa_nombre = mesas[num_mesa - 1]['nombre'] if 0 < num_mesa <= len(mesas) else f'Mesa {num_mesa}'

                hora_actual = datetime.now().strftime('%H:%M')
                notificacion = {
                    'id': len(notificaciones_pedidos) + 1,
                    'tipo': 'pedido_completado',
                    'mensaje': f'Pedido #{factura_codigo} - {mesa_nombre} completado',
                    'fecha': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'mesa_id': num_mesa,
                    'pedido_id': pedido_id,
                    'leida': False,
                    'detalles': {
                        'cliente': pedido_info['cliente_nombre'],
                        'hora': hora_actual,
                        'total_productos': pedido_info['total_productos'],
                        'total_monto': pedido_info['total_monto'],
                        'productos': [{'nombre': p.split(' x')[0], 'cantidad': int(p.split(' x')[1])} 
                                    for p in pedido_info['productos'].split(',')] if pedido_info['productos'] else []
                    }
                }
                notificaciones_pedidos.append(notificacion)

            # Eliminar la notificación asociada al pedido pagado
            notificaciones_pedidos = [n for n in notificaciones_pedidos if n.get('factura_id') != pedido_id]
            
        except Exception as e:
            print('No se puedo actualizar el estado de la factura', e)
            flash('Error al finalizar el pedido', 'error')
            return redirect(url_for('mesas1'))

        for mesa in mesas:
            if mesa['id'] == mesa_id:
                mesa['atendida'] = False
                break
        connection.commit()
        flash('Pedido finalizado exitosamente', 'success')
        return redirect(url_for('mesas1'))
    else:
        pedido_id = request.args.get('pedido_id')
        print(pedido_id)
        if not pedido_id:
            try:
                cursor.execute('''SELECT 
                    productos.id AS producto_id,
                    productos.nombre AS producto_nombre,
                    productos.precio AS producto_precio,
                    pedido_productos.cantidad AS cantidad,
                    (productos.precio * pedido_productos.cantidad) AS total,
                    pedidos.fecha_hora AS fecha, 
                    clientes.num_mesa AS mesa_id, 
                    facturas.monto AS total_monto,
                    pedidos.id AS pedido_id
                    FROM clientes
                    JOIN pedidos ON clientes.id = pedidos.clientes_id
                    JOIN pedido_productos ON pedidos.id = pedido_productos.pedido_id
                    JOIN productos ON pedido_productos.producto_id = productos.id
                    JOIN facturas ON pedidos.codigo_factura = facturas.codigo
                    WHERE clientes.num_mesa = ? AND facturas.estado = 'pendiente';''', (mesa_id,))
                info = cursor.fetchall()
                
                connection.commit()
                return render_template("finalizar.html", info = info)
            except Exception as e:
                return f"Error al cargar los datos: {str(e)}", 500
        else:
            try:
                cursor.execute('''SELECT 
                    productos.id AS producto_id,
                    productos.nombre AS producto_nombre,
                    productos.precio AS producto_precio,
                    pedido_productos.cantidad AS cantidad,
                    (productos.precio * pedido_productos.cantidad) AS total,
                    pedidos.fecha_hora AS fecha, 
                    clientes.num_mesa AS mesa_id, 
                    facturas.monto AS total_monto,
                    pedidos.id AS pedido_id
                    FROM clientes
                    JOIN pedidos ON clientes.id = pedidos.clientes_id
                    JOIN pedido_productos ON pedidos.id = pedido_productos.pedido_id
                    JOIN productos ON pedido_productos.producto_id = productos.id
                    JOIN facturas ON pedidos.codigo_factura = facturas.codigo
                    WHERE pedidos.id = ?;''', (pedido_id,))
                info = cursor.fetchall()
                print(info)
                connection.commit()
                return render_template("finalizar.html", info = info)
            except Exception as e:
                return f"Error al cargar los datos: {str(e)}",500




@app.route('/facturacion', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])  # Solo administradores pueden acceder
def facturacion():
    try:
        # Obtener parámetros de filtrado
        estado = request.args.get('estado', '').lower()
        rango_fecha = request.args.get('rango_fecha', '').lower()
        tipo_ubicacion = request.args.get('tipo_ubicacion', '').lower()
        
        cursor = connection.cursor()

        # Consulta base para facturas
        query = '''
            SELECT DISTINCT
                COALESCE(cl.nombre, 'Cliente Barra') as nombre,
                f.codigo, 
                f.monto, 
                f.estado, 
                p.fecha_hora, 
                COALESCE(cl.num_mesa, 15) as num_mesa, 
                p.id AS pedido_id,
                COALESCE(ue.nombre_user, 'Sin asignar') AS mesero,  
                f.propina,
                f.tipo_pago,
                f.tipo_tarjeta
            FROM facturas f
            JOIN pedidos p ON f.codigo = p.codigo_factura
            LEFT JOIN clientes cl ON p.clientes_id = cl.id
            LEFT JOIN usuario_empleado ue ON p.empleado_id = ue.id AND ue.rol = 'mesero'
        '''
        
        conditions = []
        params = []

        # Filtros
        if estado and estado != "todos":
            conditions.append("f.estado = ?")
            params.append(estado)

        if rango_fecha and rango_fecha != "todos":
            hoy = datetime.now()
            if rango_fecha == "hoy":
                fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
            elif rango_fecha == "ultimos_7_dias":
                fecha_inicio = hoy - timedelta(days=7)
            elif rango_fecha == "ultimo_mes":
                fecha_inicio = hoy - timedelta(days=30)
            
            if fecha_inicio:
                conditions.append("p.fecha_hora >= datetime(?, 'localtime')")
                params.append(fecha_inicio.strftime('%Y-%m-%d %H:%M:%S'))

        # Filtro por tipo de ubicación
        if tipo_ubicacion:
            if tipo_ubicacion == "mesa":
                conditions.append("(cl.nombre IS NULL OR cl.nombre != 'Cliente Barra')")
            elif tipo_ubicacion == "barra":
                conditions.append("(cl.nombre = 'Cliente Barra' OR cl.nombre IS NULL)")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Ordenar por código de factura de manera ascendente
        query += " ORDER BY CAST(f.codigo AS INTEGER) ASC"
        
        cursor.execute(query, params)
        facturas = cursor.fetchall()

        # Obtener productos para cada factura
        facturas_con_productos = []
        for factura in facturas:
            cursor.execute('''
                SELECT 
                    pr.nombre AS producto_nombre,
                    pp.cantidad,
                    pr.precio,
                    (pp.cantidad * pr.precio) AS subtotal
                FROM pedido_productos pp
                JOIN productos pr ON pp.producto_id = pr.id
                WHERE pp.pedido_id = ?
            ''', (factura['pedido_id'],))
            productos = cursor.fetchall()
            
            factura_dict = dict(factura)
            factura_dict['productos'] = productos
            facturas_con_productos.append(factura_dict)

        return render_template(
            'facturacion.html',
            facturas=facturas_con_productos,
            estado_seleccionado=estado,
            rango_fecha_seleccionado=rango_fecha,
            tipo_ubicacion_seleccionado=tipo_ubicacion
        )

    except Exception as e:
        app.logger.error(f"Error en facturacion: {str(e)}")
        flash("Ocurrió un error al obtener las facturas", "danger")
        return redirect(url_for('index'))

@app.route('/registro_empleado', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])  # Solo administradores pueden acceder
def empleados():
    if request.method == 'POST':
        nombre = request.form['nombre']
        cargo = request.form.get('cargo')
        salario = request.form['salario']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        email = request.form.get('email', '')  # Nuevo campo para email
        username = request.form.get('username', '')  # Nuevo campo para nombre de usuario
        password = request.form.get('password', '')  # Nuevo campo para contraseña

        try:
            cursor = connection.cursor()
            
            # Iniciar transacción
            cursor.execute("BEGIN TRANSACTION")
            
            # 1. Insertar en la tabla empleados
            cursor.execute("""
                INSERT INTO empleados (nombre, cargo, salario, telefono, direccion) 
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, cargo, salario, telefono, direccion))
            
            # 2. Si se proporcionaron credenciales, crear usuario
            if username and password:
                # Determinar el rol basado en el cargo
                if cargo.lower() == 'administrador':
                    rol = 'admin'
                elif cargo.lower() == 'cocinero':
                    rol = 'cocinero'
                else:
                    rol = 'mesero'
                
                cursor.execute("""
                    INSERT INTO usuario_empleado (nombre_user, contra_user, rol, email) 
                    VALUES (?, ?, ?, ?)
                """, (username, password, rol, email))
            
            # Confirmar transacción
            connection.commit()
            flash("Empleado registrado exitosamente", "success")
            return redirect(url_for('mostrar_empleados'))
            
        except Exception as e:
            # Si hay error, revertir transacción
            connection.rollback()
            flash(f"Error al registrar empleado: {str(e)}", "danger")
            return render_template('registro_empleado.html')
    else:
        return render_template('registro_empleado.html')


@app.route('/empleados')
@login_required
@role_required(['admin'])  # Solo administradores pueden acceder
def mostrar_empleados():
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM empleados")
        empleados = cursor.fetchall()
        return render_template('empleados.html', empleados=empleados)
    except:
        flash("No se pueden cargar los empleados")
        return render_template('empleados.html', empleados=[])


@app.route("/eliminar_producto/<int:id>", methods=["DELETE"])
@login_required
@role_required(['admin'])  # Solo administradores pueden acceder
def eliminar_producto(id):
    try:
        conn = sqlite3.connect("quesillos.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 200
    except Exception as e:
        print("Error eliminando producto:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/registro', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'cocinero'])  # Permitir acceso a admin y cocinero
def registro():
    cursor = connection.cursor()
    cursor.execute("SELECT id, nombre FROM productos")
    productos = cursor.fetchall()
    rango_fecha = request.args.get('rango_fecha')
    query = '''
        SELECT 
            ei.id AS entrada_id,
            ei.fecha_entrada,
            ei.cantidad_ingresada,
            ei.costo_unitario,
            ei.proveedor,
            p.id AS producto_id,
            p.nombre AS producto_nombre
        FROM entradas_inventario ei
        JOIN productos p ON ei.producto_id = p.id
    '''
    filters = []
    params = []
    if rango_fecha and rango_fecha.lower() != "todos":
        hoy = datetime.now()
        if rango_fecha == "hoy":
            inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        elif rango_fecha == "ultimos_7_dias":
            inicio = hoy - timedelta(days=7)
        elif rango_fecha == "ultimo_mes":
            inicio = hoy - timedelta(days=30)
        else:
            inicio = None
        if inicio:
            filters.append("ei.fecha_entrada >= datetime(?, 'localtime')")
            params.append(inicio.strftime('%Y-%m-%d %H:%M:%S'))
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY ei.fecha_entrada DESC"
    cursor.execute(query, params)
    entradas = cursor.fetchall()
    return render_template("registro.html", 
                         registro=entradas, 
                         productos=productos,
                         rango_fecha_seleccionado=rango_fecha)



# Ruta para mostrar formulario de edición
@app.route('/registro/editar/<int:id>', methods=['GET'])
@login_required
@role_required(['admin'])  # Solo administradores pueden acceder
def mostrar_editar_registro(id):
    cursor = connection.cursor()
    
    # Obtener la entrada específica
    cursor.execute("""
        SELECT ei.id AS entrada_id, ei.fecha_entrada, ei.cantidad_ingresada,
               ei.costo_unitario, p.id AS producto_id, p.nombre AS producto_nombre
        FROM entradas_inventario ei
        JOIN productos p ON ei.producto_id = p.id
        WHERE ei.id = ?
    """, (id,))
    entrada = cursor.fetchone()
    
    # Obtener todos los productos para el select
    cursor.execute("SELECT id, nombre FROM productos")
    productos = cursor.fetchall()
    
    return render_template("editar_registro.html", entrada=entrada, productos=productos)



@app.route('/registro/editar', methods=['POST'])
@login_required
@role_required(['admin'])  # Solo administradores pueden acceder
def editar_registro():
    # Obtener datos del formulario
    entrada_id = request.form['id']
    fecha_entrada = request.form['fecha_entrada'].replace('T', ' ')  # Convertir T en espacio
    cantidad_ingresada = int(request.form['cantidad_ingresada'])
    costo_unitario = request.form['costo_unitario']
    producto_id = request.form['producto_id']
    
    try:
        cursor = connection.cursor()
        # 1. Obtener la cantidad anterior y el producto_id anterior
        cursor.execute("SELECT cantidad_ingresada, producto_id FROM entradas_inventario WHERE id = ?", (entrada_id,))
        row = cursor.fetchone()
        cantidad_anterior = int(row['cantidad_ingresada'])
        producto_id_anterior = row['producto_id']

        # 2. Actualizar la entrada
        cursor.execute("""
            UPDATE entradas_inventario
            SET fecha_entrada = ?,
                cantidad_ingresada = ?,
                costo_unitario = ?,
                producto_id = ?
            WHERE id = ?
        """, (fecha_entrada, cantidad_ingresada, costo_unitario, producto_id, entrada_id))
        
        # 3. Si el producto es el mismo, solo ajusta la diferencia
        if producto_id == str(producto_id_anterior):
            diferencia = cantidad_ingresada - cantidad_anterior
            cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (diferencia, producto_id))
        else:
            # Si cambió el producto, resta al anterior y suma al nuevo
            cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cantidad_anterior, producto_id_anterior))
            cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad_ingresada, producto_id))

        connection.commit()
        flash("Entrada actualizada exitosamente", "success")
    except Exception as e:
        flash(f"Error al actualizar: {str(e)}", "danger")
    
    return redirect(url_for('registro'))






@app.route('/pedido/<int:pedido_id>/data', methods=['GET'])
@login_required
def get_pedido_data(pedido_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT p.id, p.nombre, pp.cantidad, p.precio
        FROM pedido_productos pp
        JOIN productos p ON pp.producto_id = p.id
        WHERE pp.pedido_id = ?
    """, (pedido_id,))
    productos = cursor.fetchall()

    order_items = [dict(row) for row in productos]
    return jsonify(orderItems=order_items)


#ruta para el renderizado de la plantilla para editar un pedido
@app.route('/editar_pedido/<int:pedido_id>', methods=['GET'])
@login_required
def editar_pedido(pedido_id):
    cursor = connection.cursor()
    try:
        # Obtener los datos del pedido
        cursor.execute('''SELECT fecha_hora AS fecha, clientes.num_mesa AS num_mesa,
                       clientes.nombre AS nombre FROM pedidos 
                       JOIN clientes ON clientes.id = pedidos.clientes_id 
                       WHERE pedidos.id = ?''', (pedido_id,))
        info = cursor.fetchall()
        num_mesa = info[0]['num_mesa']
        mesa_nombre = mesas[num_mesa]['nombre']
        # Renderizar la plantilla con los datos del pedido y los productos
        return render_template(
            'editarpedido.html',
            pedido_id=pedido_id, info=info, mesa_nombre=mesa_nombre
        )
    except Exception as e:
        print(f"Error al cargar el pedido: {e}")
        return "Error interno del servidor", 500

        

@app.route('/editar_pedido/<int:pedido_id>', methods=['POST'])
@login_required
def editar_pedidos(pedido_id):
    data = request.get_json()
    order_items = data.get('orderData')
    cliente_nombre = data.get('cliente')
    

    if not cliente_nombre:
        cliente_nombre = '-'
    if not order_items:
        return jsonify({"error": "Datos incompletos"}), 400

    cursor = connection.cursor()
    try:            
        #cursor.execute('INSERT INTO clientes (nombre, num_mesa) VALUES (?, ?)', (cliente_nombre, mesa_id))
        #cliente_id = cursor.lastrowid
        # Insertar el pedido principal
        # Actualizar productos del pedido
        cursor.execute("DELETE FROM pedido_productos WHERE pedido_id = ?", (pedido_id,))
        total_monto = 0
        for item in order_items:
            cursor.execute("""
                INSERT INTO pedido_productos (pedido_id, producto_id, cantidad)
                VALUES (?, ?, ?)
            """, (pedido_id, item['id'], item['cantidad']))
            total_monto += item['cantidad'] * item['precio']

        # Actualizar el monto total
        cursor.execute("UPDATE facturas SET monto = ? WHERE codigo = (SELECT codigo_factura FROM pedidos WHERE id = ?)", (total_monto, pedido_id))


        return jsonify({"message": "Pedido guardado con éxito", "redirect": url_for('mesas1')}), 200


    except Exception as e:
        print(f"Error al procesar el pedido: {e}")
        connection.rollback()
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/ver_factura/<int:factura_id>')
def ver_factura(factura_id):
    # Lógica para obtener la factura desde la base de datos
    conn = sqlite3.connect("quesillos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facturas WHERE codigo = ?", (factura_id,))
    factura = cursor.fetchone()
    conn.close()

    if factura:
        factura_dict = {
            "codigo": factura[0],
            "pedido_id": factura[1],
            "monto": factura[2],
            "fecha_hora": factura[3],
            "estado": factura[4]
        }
        return render_template("factura.html", factura=factura_dict)
    return "Factura no encontrada", 404

@app.route('/all_products')
@login_required
def get_all_products():
    cursor = connection.cursor()
    cursor.execute("SELECT id, nombre, precio, stock FROM productos")
    products = cursor.fetchall()
    product_list = [{"id": row[0], "nombre": row[1], "precio": row[2], "stock": row[3]} for row in products]
    return jsonify(product_list)


@app.route('/movimiento_caja', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def movimiento_caja_page():
    db = get_db()

    if request.method == 'POST':
        # Recibe JSON desde JS
        data        = request.get_json()
        monto       = data.get('monto')
        tipo        = data.get('tipo')
        descripcion = data.get('descripcion')

        if monto is None or monto <= 0 \
           or tipo not in ['entrada','salida'] \
           or not descripcion:
            return jsonify({'status':'error','message':'Datos inválidos'}), 400

        db.execute(
            "INSERT INTO movimientos_caja (tipo, descripcion, precio) VALUES (?, ?, ?)",
            (tipo, descripcion, monto)
        )
        db.commit()
        return jsonify({'status':'success'}), 200

    # GET: lee todos los movimientos
    movimientos = db.execute(
        "SELECT fecha, tipo, descripcion, precio "
        "FROM movimientos_caja ORDER BY fecha DESC"
    ).fetchall()
    return render_template('movimiento_caja.html', movimientos=movimientos)

@app.route('/debug_db')
@login_required
@role_required(['admin'])
def debug_db():
    try:
        cursor = connection.cursor()
        
        # Verificar facturas
        cursor.execute("SELECT * FROM facturas")
        facturas = cursor.fetchall()
        facturas_info = [dict(row) for row in facturas]
        
        # Verificar pedidos
        cursor.execute("SELECT * FROM pedidos")
        pedidos = cursor.fetchall()
        pedidos_info = [dict(row) for row in pedidos]
        
        # Verificar pedido_productos
        cursor.execute("SELECT * FROM pedido_productos")
        pedido_productos = cursor.fetchall()
        pedido_productos_info = [dict(row) for row in pedido_productos]
        
        # Verificar clientes
        cursor.execute("SELECT * FROM clientes")
        clientes = cursor.fetchall()
        clientes_info = [dict(row) for row in clientes]
        
        # Verificar productos
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()
        productos_info = [dict(row) for row in productos]
        
        # Consulta específica para verificar ventas de hoy
        cursor.execute("""
            SELECT f.*, p.fecha_hora, p.id as pedido_id
            FROM facturas f
            JOIN pedidos p ON f.codigo = p.codigo_factura
            WHERE date(p.fecha_hora, 'localtime') = date('now', 'localtime')
        """)
        ventas_hoy = cursor.fetchall()
        ventas_hoy_info = [dict(row) for row in ventas_hoy]
        
        debug_info = {
            'facturas': facturas_info,
            'pedidos': pedidos_info,
            'pedido_productos': pedido_productos_info,
            'clientes': clientes_info,
            'productos': productos_info,
            'ventas_hoy': ventas_hoy_info
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cocina/pedidos_pendientes')
@login_required
@role_required(['cocinero', 'admin'])  # Permitir acceso a cocineros y administradores
def cocina_pedidos_pendientes():
    cursor = connection.cursor()
    # Obtener pedidos pendientes con información de mesa y productos
    cursor.execute('''
        SELECT 
            p.id AS pedido_id,
            p.fecha_hora,
            cl.num_mesa,
            f.codigo AS factura_codigo
        FROM pedidos p
        JOIN facturas f ON p.codigo_factura = f.codigo
        JOIN clientes cl ON p.clientes_id = cl.id
        WHERE f.estado = 'pendiente' AND (p.estado IS NULL OR p.estado != 'listo')
        ORDER BY p.fecha_hora ASC
    ''')
    pedidos_pendientes = cursor.fetchall()

    pedidos_con_productos = []
    for pedido in pedidos_pendientes:
        cursor.execute('''
            SELECT 
                pr.nombre AS producto_nombre,
                pp.cantidad
            FROM pedido_productos pp
            JOIN productos pr ON pp.producto_id = pr.id
            WHERE pp.pedido_id = ?
        ''', (pedido['pedido_id'],))
        productos = cursor.fetchall()
        
        pedido_dict = dict(pedido)
        pedido_dict['productos'] = productos
        pedidos_con_productos.append(pedido_dict)

    return render_template('cocina_pedidos_pendientes.html', pedidos=pedidos_con_productos, mesas=mesas)

@app.route('/cierre-corte', methods=['GET', 'POST'])
@login_required
def cierre_corte():
    cursor = connection.cursor()

    # Calcular gastos y entradas del día SIN corte asignado
    cursor.execute("""
        SELECT IFNULL(SUM(CASE WHEN tipo = 'salida' THEN precio ELSE 0 END), 0) as gastos,
               IFNULL(SUM(CASE WHEN tipo = 'entrada' THEN precio ELSE 0 END), 0) as entradas
        FROM movimientos_caja
        WHERE date(fecha) = date('now', 'localtime') AND corte_id IS NULL
    """)
    movs = cursor.fetchone()
    gastos = movs['gastos'] or 0
    entradas = movs['entradas'] or 0

    # Calcular ventas del día
    cursor.execute("""
        SELECT 
            IFNULL(SUM(CASE WHEN f.tipo_pago = 'efectivo' THEN f.monto ELSE 0 END), 0) as venta_efectivo,
            IFNULL(SUM(CASE WHEN f.tipo_pago = 'tarjeta' AND f.tipo_tarjeta = 'bac' THEN f.monto ELSE 0 END), 0) as venta_bac,
            IFNULL(SUM(CASE WHEN f.tipo_pago = 'tarjeta' AND f.tipo_tarjeta = 'banpro' THEN f.monto ELSE 0 END), 0) as venta_banpro,
            IFNULL(SUM(f.monto), 0) as venta_total
        FROM facturas f
        JOIN pedidos p ON f.codigo = p.codigo_factura
        WHERE f.estado = 'pagada' AND date(p.fecha_hora, 'localtime') = date('now', 'localtime')
    """)
    ventas = cursor.fetchone()

    if request.method == 'POST':
        efectivo_real = float(request.form.get('efectivo', 0))
        diferencia_efectivo = efectivo_real - ventas['venta_efectivo']

        # Registrar el cierre de corte
        cursor.execute("""
            INSERT INTO cierres_corte (
                fecha, usuario_id, venta_total, venta_efectivo, venta_bac, venta_banpro,
                efectivo_real, diferencia_efectivo, gastos, entradas
            ) VALUES (
                datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            session['user_id'], ventas['venta_total'], ventas['venta_efectivo'], ventas['venta_bac'],
            ventas['venta_banpro'], efectivo_real, diferencia_efectivo, gastos, entradas
        ))
        connection.commit()

        # Obtener el id del cierre recién insertado
        cierre_id = cursor.lastrowid

        # Actualizar facturas pagadas del día para asignarles el corte_id
        cursor.execute("""
            UPDATE facturas
            SET corte_id = ?
            WHERE estado = 'pagada'
            AND codigo IN (
                SELECT f.codigo
                FROM facturas f
                JOIN pedidos p ON f.codigo = p.codigo_factura
                WHERE date(p.fecha_hora, 'localtime') = date('now', 'localtime')
                AND f.corte_id IS NULL
            )
        """, (cierre_id,))
        connection.commit()

        # Reiniciar los valores de gastos y entradas a 0 para el siguiente corte
        gastos = 0
        entradas = 0
        ventas = {'venta_total': 0, 'venta_efectivo': 0, 'venta_bac': 0, 'venta_banpro': 0}

        flash('Cierre de corte registrado exitosamente.', 'success')
        return redirect(url_for('cierre_corte'))

    # Historial de cierres
    cursor.execute("""
        SELECT c.*, u.nombre_user as usuario
        FROM cierres_corte c
        JOIN usuario_empleado u ON c.usuario_id = u.id
        ORDER BY c.fecha DESC
        LIMIT 20
    """)
    historial_cortes = cursor.fetchall()

    # Enumerar el número de cierre del día
    historial_cortes = [dict(corte) for corte in historial_cortes]
    for idx, corte in enumerate(historial_cortes, 1):
        corte['numero_cierre_dia'] = idx

    return render_template('cierre_corte.html',
                           ventas=ventas,
                           gastos=gastos,
                           entradas=entradas,
                           historial_cortes=historial_cortes)

@app.route('/cocina/marcar_listo/<int:pedido_id>', methods=['POST'])
@login_required
@role_required(['cocinero', 'admin'])
def marcar_pedido_listo(pedido_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Actualizar el estado del pedido
        cursor.execute("""
            UPDATE pedidos 
            SET listo = TRUE 
            WHERE pedido_id = %s
        """, (pedido_id,))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/barra/<int:barra_id>')
@login_required
def barra(barra_id):
    try:
        # Obtener productos disponibles
        cursor = connection.cursor()
        cursor.execute('SELECT id, nombre, precio, categoria, stock FROM productos WHERE stock > 0')
        productos = cursor.fetchall()

        # Convertir productos a lista de diccionarios
        productos_list = []
        for producto in productos:
            productos_list.append({
                'id': producto[0],
                'nombre': producto[1],
                'precio': float(producto[2]),
                'categoria': producto[3],
                'stock': producto[4]
            })

        return render_template('barra.html', 
                             barra_id=barra_id,
                             productos=productos_list)
    except Exception as e:
        print(f"Error en barra: {str(e)}")
        return redirect(url_for('mesas'))

@app.route('/procesar_pago_barra', methods=['POST'])
@login_required
def procesar_pago_barra():
    try:
        data = request.get_json()
        barra_id = data.get('barra_id')
        items = data.get('items', {})
        tipo_pago = data.get('tipo_pago', 'efectivo')
        tipo_tarjeta = data.get('tipo_tarjeta') if tipo_pago == 'tarjeta' else None
        monto_pagado = data.get('monto_pagado')

        if not items:
            return jsonify({'success': False, 'message': 'No hay items para procesar'})

        cursor = connection.cursor()
        
        # Crear cliente para la barra
        cursor.execute('''
            INSERT INTO clientes (nombre, num_mesa)
            VALUES (?, ?)
        ''', ('Cliente Barra', barra_id))
        cliente_id = cursor.lastrowid
        
        # Crear la orden
        cursor.execute('''
            INSERT INTO pedidos (fecha_hora, tipo_pedido, estado, clientes_id)
            VALUES (datetime('now', 'localtime'), 'local', 'completado', ?)
        ''', (cliente_id,))
        pedido_id = cursor.lastrowid

        # Obtener nuevo código de factura
        cursor.execute("SELECT COALESCE(MAX(codigo), 0) FROM facturas")
        last_code = cursor.fetchone()[0]
        new_code = last_code + 1

        subtotal = 0
        # Procesar cada item
        for producto_id, cantidad in items.items():
            # Obtener información del producto
            cursor.execute('SELECT precio, stock FROM productos WHERE id = ?', (producto_id,))
            producto = cursor.fetchone()
            
            if not producto:
                continue

            precio, stock = producto
            subtotal_item = precio * cantidad
            subtotal += subtotal_item

            # Insertar detalle de la orden
            cursor.execute('''
                INSERT INTO pedido_productos (pedido_id, producto_id, cantidad)
                VALUES (?, ?, ?)
            ''', (pedido_id, producto_id, cantidad))

            # Actualizar stock
            nuevo_stock = stock - cantidad
            cursor.execute('UPDATE productos SET stock = ? WHERE id = ?', (nuevo_stock, producto_id))

        # Crear factura con tipo de pago y tipo de tarjeta
        cursor.execute('''
            INSERT INTO facturas (codigo, monto, estado, fecha_creacion, tipo_pago, tipo_tarjeta)
            VALUES (?, ?, 'pagada', datetime('now', 'localtime'), ?, ?)
        ''', (new_code, subtotal, tipo_pago, tipo_tarjeta))

        # Actualizar pedido con el código de factura
        cursor.execute('UPDATE pedidos SET codigo_factura = ? WHERE id = ?', (new_code, pedido_id))

        # Crear notificación
        hora_actual = datetime.now().strftime('%H:%M')
        
        # Obtener nombres de productos
        productos_info = []
        for producto_id, cantidad in items.items():
            cursor.execute('SELECT nombre FROM productos WHERE id = ?', (producto_id,))
            producto = cursor.fetchone()
            if producto:
                productos_info.append({
                    'nombre': producto[0],
                    'cantidad': cantidad
                })

        notificacion = {
            'id': len(notificaciones_pedidos) + 1,
            'tipo': 'pedido_completado',
            'mensaje': f'Pedido #{new_code} - Barra {barra_id} completado',
            'fecha': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'pedido_id': pedido_id,
            'leida': False,
            'detalles': {
                'cliente': 'Cliente Barra',
                'hora': hora_actual,
                'total_productos': len(items),
                'total_monto': subtotal,
                'productos': productos_info
            }
        }
        notificaciones_pedidos.append(notificacion)

        connection.commit()
        cursor.close()

        return jsonify({
            'success': True, 
            'message': 'Pago procesado correctamente',
            'factura_id': new_code
        })

    except Exception as e:
        print(f"Error en procesar_pago_barra: {str(e)}")
        return jsonify({'success': False, 'message': 'Error al procesar el pago'})

@app.route('/pedidosc')
@login_required
@role_required(['admin'])
def admin_pedidos_en_curso():
    try:
        cursor = connection.cursor()

        # Consulta para obtener pedidos pendientes en mesas (y 'Para Llevar')
        # num_mesa < 15 son mesas, num_mesa = 14 es 'Para Llevar'
        query = '''
            SELECT
                p.id AS pedido_id,
                f.codigo AS factura_codigo,
                cl.num_mesa,
                p.fecha_hora,
                COALESCE(ue.nombre_user, 'Sin asignar') AS mesero,
                f.monto AS monto_actual
            FROM pedidos p
            JOIN facturas f ON p.codigo_factura = f.codigo
            JOIN clientes cl ON p.clientes_id = cl.id
            LEFT JOIN usuario_empleado ue ON p.empleado_id = ue.id
            WHERE f.estado = 'pendiente' AND cl.num_mesa IS NOT NULL AND cl.num_mesa <= 14
            ORDER BY cl.num_mesa ASC, p.fecha_hora ASC
        '''

        cursor.execute(query)
        pedidos_en_curso = cursor.fetchall()

        pedidos_con_info = []
        for pedido in pedidos_en_curso:
            pedido_dict = dict(pedido)
            # Calcular tiempo transcurrido
            fecha_hora_pedido = datetime.strptime(pedido['fecha_hora'], '%Y-%m-%d %H:%M:%S')
            tiempo_transcurrido = datetime.now() - fecha_hora_pedido
            # Formatear tiempo transcurrido (ej: HH:MM:SS)
            segundos_totales = int(tiempo_transcurrido.total_seconds())
            horas = segundos_totales // 3600
            minutos = (segundos_totales % 3600) // 60
            segundos = segundos_totales % 60
            pedido_dict['tiempo_transcurrido'] = f'{horas:02d}:{minutos:02d}:{segundos:02d}'

            # Obtener el nombre de la mesa/ubicación
            mesa_id = pedido['num_mesa']
            mesa_info = next((m for m in mesas if m['id'] == mesa_id), None)
            pedido_dict['nombre_ubicacion'] = mesa_info['nombre'] if mesa_info else f'Mesa {mesa_id}'

            pedidos_con_info.append(pedido_dict)

        return render_template(
            'admin_pedidos_en_curso.html',
            pedidos=pedidos_con_info
        )

    except Exception as e:
        app.logger.error(f"Error en admin_pedidos_en_curso: {str(e)}")
        flash("Ocurrió un error al obtener los pedidos en curso", "danger")
        return redirect(url_for('index'))

@app.route('/respaldos', methods=['GET'])
@login_required
@role_required(['admin'])
def respaldos():
    """
    Muestra la página de respaldos y permite crear respaldos manuales
    """
    # Obtener lista de respaldos existentes
    backups = sorted(BACKUP_DIR.glob('quesillos_backup_*.db'), reverse=True)
    respaldos_list = []
    
    for backup in backups:
        # Obtener información del archivo
        stats = backup.stat()
        respaldos_list.append({
            'nombre': backup.name,
            'fecha': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'tamano': f"{stats.st_size / 1024:.1f} KB"
        })
    
    return render_template('respaldos.html', respaldos=respaldos_list)

@app.route('/crear_respaldo', methods=['POST'])
@login_required
@role_required(['admin'])
def crear_respaldo():
    """
    Crea un respaldo manual de la base de datos
    """
    if create_backup():
        flash('Respaldo creado exitosamente', 'success')
    else:
        flash('Error al crear el respaldo', 'error')
    
    return redirect(url_for('respaldos'))

@app.route('/descargar_respaldo/<nombre>')
@login_required
@role_required(['admin'])
def descargar_respaldo(nombre):
    """
    Permite descargar un respaldo específico
    """
    backup_path = BACKUP_DIR / nombre
    if backup_path.exists():
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=nombre
        )
    flash('Respaldo no encontrado', 'error')
    return redirect(url_for('respaldos'))

if __name__ == '__main__':
    app.run(debug=True)
