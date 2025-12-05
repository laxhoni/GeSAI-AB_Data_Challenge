import os
import re
import secrets
import base64
import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_DIR = os.path.join(BASE_DIR, 'keys')
os.makedirs(KEYS_DIR, exist_ok=True)

# Rutas de archivos de claves
PATH_CLAVE_PRIVADA = os.path.join(KEYS_DIR, 'gesai_private_key.pem')
PATH_CERTIFICADO = os.path.join(KEYS_DIR, 'gesai_certificate.pem')
PATH_CLAVE_SIMETRICA = os.path.join(KEYS_DIR, 'secret.key')

# ==============================================================================
# 1. GESTIÓN DE CLAVES SIMÉTRICAS (Para Cifrar Datos en BBDD)
# ==============================================================================
def _cargar_o_crear_clave_simetrica():
    """Carga la clave maestra AES. Si no existe, la crea."""
    if os.path.exists(PATH_CLAVE_SIMETRICA):
        with open(PATH_CLAVE_SIMETRICA, 'rb') as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(PATH_CLAVE_SIMETRICA, 'wb') as key_file:
            key_file.write(key)
        print("🔑 Nueva clave maestra de cifrado generada.")
        return key

# Instancia global del cifrador (Singleton)
_cipher_suite = Fernet(_cargar_o_crear_clave_simetrica())

def cifrar_pii(texto):
    """
    Cifra Información Personal Identificable (PII) para guardar en SQL.
    Entrada: String (ej: 'Juan Pérez')
    Salida: String cifrado en base64
    """
    if not texto: return None
    try:
        # Fernet usa AES-128-CBC con HMAC (Integridad + Confidencialidad)
        return _cipher_suite.encrypt(texto.encode('utf-8')).decode('utf-8')
    except Exception as e:
        print(f"Error cifrando: {e}")
        return None

def descifrar_pii(texto_cifrado):
    """
    Descifra datos leídos de SQL para mostrarlos en la App/PDF.
    """
    if not texto_cifrado: return None
    try:
        return _cipher_suite.decrypt(texto_cifrado.encode('utf-8')).decode('utf-8')
    except Exception:
        return "[DATOS CORRUPTOS O CLAVE INCORRECTA]"

# ==============================================================================
# 2. GESTIÓN DE CONTRASEÑAS (Hashing Seguro con Scrypt)
# ==============================================================================
def hashear_password(password_plano):
    """
    Genera un hash seguro usando Scrypt.
    Retorna: string formato 'salt_hex$hash_hex'
    """
    salt = os.urandom(16)
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend()
    )
    hash_bytes = kdf.derive(password_plano.encode('utf-8'))
    
    # Guardamos Salt y Hash juntos separados por $
    return f"{salt.hex()}${hash_bytes.hex()}"

def verificar_password(password_plano, hash_guardado):
    """
    Verifica si la contraseña coincide con el hash guardado.
    """
    try:
        salt_hex, hash_hex = hash_guardado.split('$')
        salt = bytes.fromhex(salt_hex)
        hash_original = bytes.fromhex(hash_hex)
        
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=default_backend()
        )
        kdf.verify(password_plano.encode('utf-8'), hash_original)
        return True
    except Exception:
        return False

# ==============================================================================
# 3. IDENTIDAD DIGITAL Y FIRMA (PKI)
# ==============================================================================
def generar_identidad_corporativa():
    """Genera Clave Privada y Certificado Autofirmado (CA) si no existen."""
    if os.path.exists(PATH_CLAVE_PRIVADA) and os.path.exists(PATH_CERTIFICADO):
        return # Ya existen

    print("🔐 Generando PKI Corporativa para GeSAI...")
    
    # 1. Generar Clave Privada RSA
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # 2. Datos del Certificado (Identity)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"ES"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Barcelona"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Aigües de Barcelona"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"GeSAI Root CA"),
    ])

    # 3. Construir Certificado
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).sign(private_key, hashes.SHA256(), default_backend())

    # 4. Guardar en disco
    with open(PATH_CLAVE_PRIVADA, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open(PATH_CERTIFICADO, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print("✅ Identidad Digital creada en /src/keys/")

def firmar_digitalmente(datos_bytes):
    """
    Firma bytes (ej. contenido PDF) usando la clave privada de GeSAI.
    Retorna: Firma en Hexadecimal.
    """
    if not os.path.exists(PATH_CLAVE_PRIVADA):
        generar_identidad_corporativa()

    with open(PATH_CLAVE_PRIVADA, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(), password=None, backend=default_backend()
        )

    signature = private_key.sign(
        datos_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature.hex()

# ==============================================================================
# 4. UTILIDADES DE SEGURIDAD EXTRA
# ==============================================================================
def generar_token_seguro():
    """Genera un token aleatorio criptográficamente fuerte (URL-safe)."""
    return secrets.token_urlsafe(32)

def sanitizar_input_texto(texto):
    """
    Limpieza básica de inputs para prevenir XSS/Inyección en logs.
    NOTA: La Inyección SQL se previene usando '?' en las queries, no aquí.
    """
    if not isinstance(texto, str): return str(texto)
    # Eliminar caracteres peligrosos comunes
    return texto.replace("'", "").replace('"', "").replace(";", "").strip()

# Inicialización automática al importar
generar_identidad_corporativa()

# ==============================================================================
# 5. POLÍTICA DE CONTRASEÑAS (NUEVO)
# ==============================================================================
def validar_fortaleza_password(password):
    """
    Verifica que la contraseña cumpla los requisitos de seguridad:
    - Mínimo 12 caracteres (OWASP recomienda 12+).
    - Al menos 1 mayúscula.
    - Al menos 1 minúscula.
    - Al menos 1 número.
    - Al menos 1 carácter especial (!@#$%^&*...).
    - No estar en la lista negra de contraseñas comunes.
    
    Retorna: (EsValida: bool, MensajeError: str)
    """
    if len(password) < 12:
        return False, "La contraseña es muy corta. Mínimo 12 caracteres."

    if not re.search(r"[A-Z]", password):
        return False, "Debe contener al menos una letra MAYÚSCULA."

    if not re.search(r"[a-z]", password):
        return False, "Debe contener al menos una letra minúscula."

    if not re.search(r"\d", password):
        return False, "Debe contener al menos un NÚMERO."

    if not re.search(r"[ !@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        return False, "Debe contener al menos un CARÁCTER ESPECIAL (!@#$%)."

    # Lista negra básica
    blacklist = ['123456789012', 'password1234', 'admin1234567', 'gesai1234567']
    if password.lower() in blacklist:
        return False, "Esa contraseña es demasiado común o predecible."

    return True, "Contraseña fuerte."