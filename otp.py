import random
import os
from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# Configurar Flask-Mail con variables de entorno
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Obtiene el correo desde .env
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Obtiene la contraseña desde .env

mail = Mail(app)

def generate_otp():
    """Genera un código OTP de 6 dígitos"""
    return str(random.randint(100000, 999999))

def send_otp(email, otp):
    """Envía un código OTP por correo electrónico"""
    with app.app_context():
        msg = Message('Tu código OTP', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f'Tu código de verificación es: {otp}'
        try:
            mail.send(msg)
            print(f"✅ OTP enviado a {email}")
        except Exception as e:
            print(f"❌ Error al enviar OTP: {e}")

# Generar y enviar OTP de prueba
stored_otp = generate_otp()
send_otp('aleman.galeman@gmail.com', stored_otp)

# Simulación de ingreso de usuario
user_input = input("Ingresa el código OTP: ")
if user_input == stored_otp:
    print("✅ Acceso permitido")
else:
    print("❌ Código incorrecto")
