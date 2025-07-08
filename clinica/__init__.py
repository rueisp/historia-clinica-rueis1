# clinica/__init__.py

import os
from flask import Flask
from .extensions import db, migrate, login_manager
from dotenv import load_dotenv

load_dotenv()

def create_app():
    """Application Factory Function"""
    
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'una-clave-secreta-de-desarrollo-muy-dificil')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:23456@localhost:5432/clinica')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # En producción (Render), las cookies de sesión deben ser seguras.
    # La variable RENDER es automáticamente establecida por la plataforma.
    if os.getenv('RENDER'):
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    else:
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


    # --- CONFIGURACIÓN DE CARPETAS DE SUBIDA PARA RENDER Y LOCAL ---
    
    # Ruta base para el almacenamiento persistente en el disco de Render
    STORAGE_DIR = '/var/data/clinica/uploads'
    
    # Si no estamos en Render (estamos en local), usamos la carpeta 'static'
    # Esta es una forma de detectar si estamos en el entorno de Render
    if not os.path.exists('/var/data/clinica'):
        # En local, guardaremos dentro de 'clinica/static/uploads'
        STORAGE_DIR = os.path.join(app.root_path, 'static', 'uploads')

    # Definimos las rutas de subida basadas en el directorio de almacenamiento
    UPLOAD_FOLDER_IMAGENES = os.path.join(STORAGE_DIR, 'imagenes')
    UPLOAD_FOLDER_DENTIGRAMAS = os.path.join(STORAGE_DIR, 'dentigramas')

    # Aseguramos que los directorios existan al iniciar la app
    os.makedirs(UPLOAD_FOLDER_IMAGENES, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER_DENTIGRAMAS, exist_ok=True)

    app.config['UPLOAD_FOLDER_IMAGENES'] = UPLOAD_FOLDER_IMAGENES
    app.config['UPLOAD_FOLDER_DENTIGRAMAS'] = UPLOAD_FOLDER_DENTIGRAMAS
    # --- FIN DE LA CONFIGURACIÓN DE CARPETAS ---

    
    # --- 2. INICIALIZAR EXTENSIONES CON LA APP (Sin cambios) ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- 3. REGISTRAR BLUEPRINTS (RUTAS) (Sin cambios) ---
    with app.app_context():
        from .models import Usuario
        
        @login_manager.user_loader
        def load_user(user_id):
            return Usuario.query.get(int(user_id))


        # --- SECCIÓN DE IMPORTACIONES DE BLUEPRINTS ---
        # Se importan TODAS las variables de blueprint de cada archivo de rutas
        
        from .routes.main import main_bp
        from .routes.pacientes import pacientes_bp
        from .routes.pacientes_evoluciones import evoluciones_bp
        from .routes.pacientes_ajax import ajax_bp
        
        # --- ¡¡AQUÍ ESTÁ LA LÍNEA CLAVE QUE PROBABLEMENTE FALTABA O ESTABA MAL!! ---
        from .routes.pacientes_citas import citas_paciente_bp 
        
        from .routes.calendario import calendario_bp
        from .routes.export import export_bp
        from .routes.papelera import papelera_bp

        # --- SECCIÓN DE REGISTRO DE BLUEPRINTS ---
        # Se registran TODAS las variables de blueprint importadas
        
        app.register_blueprint(main_bp)
        app.register_blueprint(pacientes_bp)
        app.register_blueprint(evoluciones_bp)
        app.register_blueprint(ajax_bp)
        
        # --- ¡¡Y AQUÍ TAMBIÉN!! ---
        app.register_blueprint(citas_paciente_bp)
        
        app.register_blueprint(calendario_bp, url_prefix='/calendario')
        app.register_blueprint(export_bp, url_prefix='/export')
        app.register_blueprint(papelera_bp, url_prefix='/papelera')
        
    return app