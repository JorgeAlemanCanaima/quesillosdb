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


# Cargar variables de entorno
load_dotenv()

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


@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if value is None:
        return ""
    
    if isinstance(value, str):
        # Eliminar la 'T' si existe
        value = value.replace('T', ' ')
        try:
            # Intentar parsear diferentes formatos
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M')
            except ValueError:
                return value  # Devuelve el valor original si no se puede parsear
    
    # Formatear la fecha
    return value.strftime(format)

app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave segura en producción

# Configuración de sesión
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuración de la base de datos
database_path = "quesillos.db"
connection = sqlite3.connect(database_path, check_same_thread=False)
connection.row_factory = sqlite3.Row

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

@app.route('/historial')
@login_required
@role_required(['admin']) 
def historial():
    try:
        cursor = connection.cursor()

        # Propinas de hoy
        cursor.execute("""
            SELECT IFNULL(SUM(propina), 0) as total
            FROM facturas
            WHERE DATE(fecha_creacion) = DATE('now')
        """)
        propinas_hoy = cursor.fetchone()['total']

       

        # Propinas de este mes
        cursor.execute("""
            SELECT IFNULL(SUM(propina), 0) as total
            FROM facturas
            WHERE strftime('%Y-%m', fecha_creacion) = strftime('%Y-%m', 'now')
        """)
        propinas_mes = cursor.fetchone()['total']


        # Ventas de hoy 
        cursor.execute("""
            SELECT SUM(f.monto) as total 
            FROM facturas f
            JOIN pedidos p ON f.codigo = p.codigo_factura
            WHERE date(p.fecha_hora) = date('now') 
            AND f.estado = 'pagada'
        """)
        ventas_dia = cursor.fetchone()[0] or 0

        # Órdenes de hoy
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pedidos 
            WHERE date(fecha_hora) = date('now')
        """)
        ordenes_dia = cursor.fetchone()[0] or 0

        # Clientes únicos hoy
        cursor.execute("""
            SELECT COUNT(DISTINCT clientes_id) 
            FROM pedidos 
            WHERE date(fecha_hora) = date('now')
        """)
        clientes_dia = cursor.fetchone()[0] or 0

        # Ventas mensuales
        cursor.execute("""
            SELECT strftime('%m', p.fecha_hora) as mes, SUM(f.monto) as total
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

        # Mejores meses (top 5)
        cursor.execute("""
            SELECT strftime('%m', p.fecha_hora) as mes, SUM(f.monto) as total
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
                    # Establecer la sesión del usuario
                    session['user_id'] = user['id']
                    session['username'] = user['nombre_user']
                    session['rol'] = user['rol']
                    flash("OTP verificado correctamente. Bienvenido!", "success")
                    return redirect(url_for('mesas1'))
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





# Ruta para la página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT * FROM usuario_empleado WHERE nombre_user = ? AND contra_user = ?
            """, (username, password))
            user = cursor.fetchone()
            
            if not user:
                flash("Usuario o contraseña incorrectos.", "error")
                return redirect(url_for('login'))

            else:
                session['user_id'] = user[0]
                session['username'] = username
                session['rol'] = user['rol']
                print("Sesión iniciada correctamente")
                print("User ID guardado en la sesión:", session.get('user_id'))
                print("Rol guardado en la sesión:", session.get('rol'))

                return redirect(url_for('mesas1'))
        except:
            print("Error en la consulta:")
            flash("Error al procesar la solicitud. Intenta nuevamente.")
            return redirect(url_for('login'))
    
    return render_template('login.html')



#cierre de sesion
@app.route("/logout", methods=['POST'])
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# Ruta para la página principal
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
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
                INSERT INTO productos (nombre, precio, categoria) VALUES (?, ?, ?)
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
@role_required(['admin', 'mesero'])  # Solo administradores pueden acceder
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
@role_required(['admin', 'mesero'])  # Permitir acceso a admin y mesero
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
    
    cursor = connection.cursor()
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
def products():    
    mesa_id = request.args.get('mesa_id')
    print(mesa_id)
    mesa_nombre = mesas[int(mesa_id) - 1]['nombre']
    
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('pedidos.html', mesa_id=mesa_id, fecha=fecha, mesa_nombre=mesa_nombre)

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

#ruta del boton para atender una mesa en especifico
#se encarga de actualizar el estado de la mesa y hacer todas las inserciones necesarias
#en las tablas de pedido, facturas, pedido_productos y clientes
@app.route('/atender_mesa/<int:mesa_id>', methods=['POST'])
@login_required
def atender_mesa(mesa_id):
    data = request.get_json()
    order_data = data.get('orderData')
    cliente_nombre = data.get('cliente')
    print(cliente_nombre)

    if not cliente_nombre:
        cliente_nombre = '-'
    if not order_data:
        return jsonify({"error": "Datos incompletos"}), 400

    cursor = connection.cursor()
    try:
        # Verificar stock disponible antes de procesar el pedido
        for item in order_data:
            cursor.execute("SELECT stock FROM productos WHERE id = ?", (item['id'],))
            producto = cursor.fetchone()
            if not producto or producto['stock'] < item['cantidad']:
                return jsonify({
                    "error": f"Stock insuficiente para el producto ID {item['id']}"
                }), 400

        # Cambiar el estado de la mesa
        for mesa in mesas:
            if mesa_id > 13:
                break
            if mesa['id'] == mesa_id:
                mesa['atendida'] = True
                break
        
        if mesa_id == 13:
            estado_pedido = 'domicilio'
        else:
            estado_pedido = 'local'
        cursor.execute('INSERT INTO clientes (nombre, num_mesa) VALUES (?, ?)', (cliente_nombre, mesa_id))
        cliente_id = cursor.lastrowid
        # Insertar el pedido principal
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(''' SELECT codigo FROM facturas ORDER BY codigo DESC LIMIT 1''')
        codigo = cursor.fetchone()
        codigo = codigo['codigo'] + 1
        print(codigo)
        
        cursor.execute("""
            INSERT INTO pedidos (fecha_hora, tipo_pedido, empleado_id, clientes_id, codigo_factura)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha, estado_pedido, 1, cliente_id, codigo))  

        # Obtener el ID del último pedido para la insercion del nuevo pedido con el id correspondiente
        pedido_id = cursor.lastrowid
        total_monto = 0
        # Insertar los productos del pedido y actualizar el stock
        for item in order_data:
            cursor.execute("""
                INSERT INTO pedido_productos (pedido_id, producto_id, cantidad)
                VALUES (?, ?, ?)
            """, (pedido_id, item['id'], item['cantidad']))
            total_monto += float(item['total'])
            
            # Actualizar el stock del producto
            cursor.execute("""
                UPDATE productos 
                SET stock = stock - ? 
                WHERE id = ?
            """, (item['cantidad'], item['id']))
        
        print(total_monto)
        cursor.execute('''INSERT INTO FACTURAS (codigo, monto, estado) 
                       VALUES (?, ?, ?)''', (codigo, total_monto, 'pendiente'))
             
        # Confirmar cambios
        connection.commit()

        return jsonify({"message": "Pedido guardado con éxito", "redirect": url_for('mesas1')}), 200

    except Exception as e:
        print(f"Error al procesar el pedido: {e}")
        connection.rollback()
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/finalizar/<int:mesa_id>', methods=['GET', 'POST'])
@login_required
def finalizar(mesa_id):
    cursor = connection.cursor()
    if request.method == 'POST':
        print(mesa_id)
        try:
            #extraemos el id del pedido para poder actualizar el estado de la factura
            pedido_id = request.args.get('pedido_id')
            #esto es para el apartado de finalizar desde la venta de mesas
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
            #finalizar desde el apartado de historial de pedidos
            print(f'ID del pedido {pedido_id}')

            incluir_propina = request.form.get('propina')  
            print(f'Valor del checkbox {incluir_propina}')

            # Calcular la propina, por ejemplo, 10% del total
            cursor.execute('SELECT monto FROM facturas WHERE codigo = (SELECT codigo_factura FROM pedidos WHERE pedidos.id = ?)', (pedido_id,))
            factura = cursor.fetchone()

            #primero extraemos el monto que estaba asignado en la factura
            total_factura = factura[0]
            propina = total_factura * 0.10 if incluir_propina else 0
            print(propina)
            nuevo_total = total_factura + propina
            
            # ACTUALIZACIÓN MODIFICADA PARA INCLUIR LA COLUMNA PROPINA
            cursor.execute('''UPDATE facturas 
                          SET estado = 'pagada', 
                              monto = ?,
                              propina = ?
                          WHERE codigo = (SELECT codigo_factura FROM pedidos WHERE pedidos.id = ?)''', 
                          (nuevo_total, propina, pedido_id))
            
        #manejo de errores 
        except Exception as e:
            print('No se puedo actualizar el estado de la factura', e)
        for mesa in mesas:
            if mesa['id'] == mesa_id:
                mesa['atendida'] = False
                break
        connection.commit()
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
        
        cursor = connection.cursor()

        # Consulta base para facturas
        query = '''
            SELECT 
                cl.nombre,
                f.codigo, 
                f.monto, 
                f.estado, 
                p.fecha_hora, 
                cl.num_mesa, 
                p.id AS pedido_id,
                e.nombre AS mesero,
                f.propina  
            FROM facturas f
            JOIN pedidos p ON f.codigo = p.codigo_factura
            JOIN clientes cl ON p.clientes_id = cl.id
            JOIN empleados e ON p.empleado_id = e.id
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
                conditions.append("p.fecha_hora >= ?")
                params.append(fecha_inicio)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY p.fecha_hora DESC"
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
            rango_fecha_seleccionado=rango_fecha
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

        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO empleados (nombre, cargo, salario, telefono, direccion) 
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, cargo, salario, telefono, direccion))
            connection.commit()
            return redirect(url_for('mostrar_empleados'))
        except: 
            flash("No se puede ingresar el empleado")
            return render_template('registro_empleado.html')  # ✅ corregido aquí
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
@role_required(['admin'])  # Solo administradores pueden acceder
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
            filters.append("ei.fecha_entrada >= ?")
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
    cantidad_ingresada = request.form['cantidad_ingresada']
    costo_unitario = request.form['costo_unitario']
    producto_id = request.form['producto_id']
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE entradas_inventario
            SET fecha_entrada = ?,
                cantidad_ingresada = ?,
                costo_unitario = ?,
                producto_id = ?
            WHERE id = ?
        """, (fecha_entrada, cantidad_ingresada, costo_unitario, producto_id, entrada_id))
        
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


        


    except Exception as e:
        print(f"Error al procesar el pedido: {e}")
        connection.rollback()
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/all_products')
@login_required
def get_all_products():
    cursor = connection.cursor()
    cursor.execute("SELECT id, nombre, precio, stock FROM productos")
    products = cursor.fetchall()
    product_list = [{"id": row[0], "nombre": row[1], "precio": row[2], "stock": row[3]} for row in products]
    return jsonify(product_list)

if __name__ == '__main__':
    app.run(debug=True)