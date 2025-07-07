# clinica/__init__.py

import os
from flask import Flask
from .extensions import db, migrate, login_manager
# No es necesario importar Usuario aquí si se importa dentro de la función

def create_app():
    """Application Factory Function"""
    
    app = Flask(__name__)

    # --- 1. CONFIGURACIÓN DE LA APP ---
    app.config['SECRET_KEY'] = '23456'
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:23456@localhost:5432/clinica'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['UPLOAD_FOLDER_DENTIGRAMAS'] = os.path.join(app.static_folder, 'img', 'pacientes', 'dentigramas')
    app.config['UPLOAD_FOLDER_IMAGENES'] = os.path.join(app.static_folder, 'img', 'pacientes', 'imagenes')

    os.makedirs(app.config['UPLOAD_FOLDER_DENTIGRAMAS'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_IMAGENES'], exist_ok=True)

    # --- 2. INICIALIZAR EXTENSIONES CON LA APP ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- 3. REGISTRAR BLUEPRINTS (RUTAS) ---
    with app.app_context():
        # Importa el modelo Usuario aquí para que el user_loader lo encuentre
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