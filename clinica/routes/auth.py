# clinica/routes/main.py

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, current_app
)
from flask_login import login_user, logout_user, login_required, current_user

# Importa el objeto 'db' de tu archivo de extensiones
from ..extensions import db 
# Importa los modelos que necesitarás
from ..models import Usuario, AuditLog, Cita, Paciente

# Importa funciones auxiliares que estaban en app.py (si las necesitas aquí)
# Si get_index_panel_data sigue siendo muy grande, podría vivir en un archivo 'utils.py'
from sqlalchemy import func, case, or_
from sqlalchemy.orm import joinedload
from datetime import date, datetime
import locale

# --- Definición del Blueprint ---
# 'main' es el nombre que usaremos en url_for, ej: url_for('main.index')
main_bp = Blueprint('main', __name__, template_folder='../templates')


def get_index_panel_data():
    """
    Función para obtener los datos necesarios para el panel de inicio.
    Esta función ahora es parte de este blueprint.
    """
    # ... (Copiamos la función completa aquí, pero con una mejora clave) ...
    # Usamos current_app.logger en lugar de app.logger
    
    hoy = date.today()
    datos_panel = {}

    # 1. Fecha actual formateada
    # Esta lógica de locale es compleja, la mantenemos como la tenías
    fecha_formateada_buffer = None 
    locale_original_time = locale.getlocale(locale.LC_TIME)
    try:
        locales_a_intentar_es = ['es_ES.UTF-8', 'es_ES', 'es', 'Spanish_Spain.1252', 'Spanish']
        configurado_es = False
        for loc_es in locales_a_intentar_es:
            try:
                locale.setlocale(locale.LC_TIME, loc_es)
                fecha_formateada_buffer = hoy.strftime("%A, %d de %B de %Y").capitalize()
                configurado_es = True
                break
            except locale.Error:
                continue
        if not configurado_es: 
            locale.setlocale(locale.LC_TIME, '') 
            fecha_formateada_buffer = hoy.strftime("%A, %d de %B de %Y").capitalize()
    except Exception as e:
        current_app.logger.error(f"Error excepcional al formatear fecha_actual_formateada: {e}")
        fecha_formateada_buffer = hoy.strftime("%A, %d %B %Y").capitalize()
    finally:
        if locale_original_time != (None, None):
            try:
                locale.setlocale(locale.LC_TIME, locale_original_time)
            except locale.Error:
                pass
    datos_panel['fecha_actual_formateada'] = fecha_formateada_buffer

    # 2. Estadísticas: Citas de hoy
    citas_hoy_count = db.session.query(func.count(Cita.id))\
        .join(Paciente, Cita.paciente_id == Paciente.id)\
        .filter(
            Cita.fecha == hoy,
            Cita.is_deleted == False,
            Paciente.is_deleted == False
        ).scalar() or 0
    datos_panel['estadisticas'] = {'citas_hoy': citas_hoy_count}
    
    # ... (El resto de la lógica de get_index_panel_data sigue aquí sin cambios)...
    # Asegúrate de que todas las dependencias como Cita, Paciente, db, etc., estén importadas.
    # Esta es una versión abreviada para no pegar todo de nuevo.
    # Solo pega el resto de tu función original aquí.
    
    # Ejemplo del final de la función
    citas_de_hoy_lista = Cita.query.options(joinedload(Cita.paciente))\
        .join(Paciente, Cita.paciente_id == Paciente.id)\
        .filter(Cita.fecha == hoy, Cita.is_deleted == False, Paciente.is_deleted == False)\
        .order_by(Cita.hora).all()
        
    citas_hoy_procesadas = []
    for cita_item in citas_de_hoy_lista:
        citas_hoy_procesadas.append({
            'id': cita_item.id,
            'hora_formateada': cita_item.hora.strftime("%I:%M %p"), 
            'paciente_nombre_completo': f"{cita_item.paciente.nombres} {cita_item.paciente.apellidos}",
            'motivo': getattr(cita_item, 'motivo', "No especificado"),
            'estado': getattr(cita_item, 'estado', 'pendiente')
        })
    datos_panel['citas_del_dia'] = citas_hoy_procesadas

    return datos_panel


# --- Definición de las Rutas usando el Blueprint ---

@main_bp.route("/")
@login_required # ¡Protegemos la página principal!
def index():
    try:
        panel_data = get_index_panel_data() 
    except Exception as e:
        current_app.logger.error(f"Error al obtener datos del panel: {e}", exc_info=True)
        panel_data = {}
        flash("Hubo un error al cargar los datos del panel de inicio.", "danger")

    try:
        ultimas_acciones = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5).all()
    except Exception as e:
        current_app.logger.error(f"Error al obtener las últimas acciones de auditoría: {e}", exc_info=True)
        ultimas_acciones = []

    template_data = {
        **panel_data,
        'ultimas_acciones': ultimas_acciones
        # 'current_user' ya está disponible globalmente en las plantillas gracias a Flask-Login
    }
    
    return render_template("index.html", **template_data)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Apunta a la función 'index' dentro del blueprint 'main'

    if request.method == 'POST':
        username_o_email = request.form.get('usuario')
        contrasena = request.form.get('contrasena')
        remember_me = request.form.get('remember_me') is not None 

        if not username_o_email or not contrasena:
            flash('Por favor, ingresa tu usuario y contraseña.', 'warning')
            return render_template('login.html')

        # La consulta a la DB usa el objeto 'db' que importamos
        usuario_encontrado = Usuario.query.filter(
            or_(Usuario.username == username_o_email, Usuario.email == username_o_email)
        ).first()
        
        if usuario_encontrado and usuario_encontrado.check_password(contrasena):
            login_user(usuario_encontrado, remember=remember_me)
            flash('Has iniciado sesión correctamente.', 'success')
            
            next_page = request.args.get('next')
            # Redirigir a 'next_page' o al index si no hay 'next'
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Credenciales inválidas. Por favor, verifica tu usuario y contraseña.', 'danger')

    return render_template('login.html')


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('main.login')) # Redirige a la página de login del blueprint 'main'

