# clinica/utils.py
import os
import calendar
import locale
from datetime import date, datetime
from sqlalchemy import func, case
from sqlalchemy.orm import joinedload
from .extensions import db
from .models import Paciente, Cita
from flask import current_app


nombres_meses = [calendar.month_name[i] for i in range(1, 13)]


# Extensiones permitidas para imágenes
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def eliminar_imagen(ruta_imagen_relativa):
    """
    Elimina de forma segura un archivo de la carpeta static.
    La ruta debe ser relativa a la carpeta 'static', 
    ej: 'img/pacientes/imagenes/archivo.jpg'
    """
    if not ruta_imagen_relativa:
        return

    try:
        # Construye la ruta absoluta usando la configuración de la app actual
        ruta_absoluta = os.path.join(current_app.static_folder, ruta_imagen_relativa)
        
        if os.path.exists(ruta_absoluta):
            os.remove(ruta_absoluta)
            # Usar el logger de Flask es mejor que usar print
            current_app.logger.info(f"Archivo eliminado exitosamente: {ruta_absoluta}")
        else:
            current_app.logger.warning(f"Se intentó eliminar un archivo que no existe: {ruta_absoluta}")
    except Exception as e:
        current_app.logger.error(f"Error crítico al eliminar imagen {ruta_imagen_relativa}: {e}", exc_info=True)

def convertir_a_fecha(valor_str):
    """Convierte un string en formato 'YYYY-MM-DD' a un objeto date."""
    if not valor_str or not isinstance(valor_str, str):
        return None
    try:
        return datetime.strptime(valor_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # Devuelve None si el string está vacío o el formato es incorrecto
        return None        

def get_index_panel_data():
    """Función para obtener los datos necesarios para el panel de inicio."""
    hoy = date.today()
    datos_panel = {}

    # 1. Fecha actual formateada (TU CÓDIGO ACTUAL - SIN CAMBIOS AQUÍ)
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
        print(f"Error excepcional al formatear fecha_actual_formateada: {e}")
        fecha_formateada_buffer = hoy.strftime("%A, %d %B %Y").capitalize()
    finally:
        if locale_original_time != (None, None):
            try:
                locale.setlocale(locale.LC_TIME, locale_original_time)
            except locale.Error:
                print(f"Advertencia: No se pudo restaurar el locale original {locale_original_time} para LC_TIME.")
    datos_panel['fecha_actual_formateada'] = fecha_formateada_buffer

    # 2. Estadísticas: Citas de hoy
    # Contar solo citas activas de pacientes activos
    citas_hoy_count = db.session.query(func.count(Cita.id))\
        .join(Paciente, Cita.paciente_id == Paciente.id)\
        .filter(
            Cita.fecha == hoy,
            Cita.is_deleted == False,         # <<<--- FILTRO AÑADIDO --- >>>
            Paciente.is_deleted == False      # <<<--- FILTRO AÑADIDO --- >>>
        ).scalar() or 0
    datos_panel['estadisticas'] = {'citas_hoy': citas_hoy_count}

    # 3. Próxima cita
    # Buscar solo citas activas de pacientes activos
    ahora = datetime.now()
    proxima_cita_obj = Cita.query.options(joinedload(Cita.paciente))\
        .join(Paciente, Cita.paciente_id == Paciente.id)\
        .filter(
            Cita.fecha >= hoy,
            Cita.is_deleted == False,         # <<<--- FILTRO AÑADIDO --- >>>
            Paciente.is_deleted == False,     # <<<--- FILTRO AÑADIDO --- >>>
            case((Cita.fecha == hoy, Cita.hora > ahora.time()), else_=(Cita.fecha > hoy))
        )\
        .order_by(Cita.fecha, Cita.hora)\
        .first()
    
    proxima_cita_data = None
    if proxima_cita_obj:
        # Formateo de fecha para proxima_cita (TU CÓDIGO ACTUAL - SIN CAMBIOS AQUÍ)
        fecha_cita_str_buffer = None
        # locale_original_time ya fue guardado al inicio de la función
        try:
            locales_a_intentar_es_cita = ['es_ES.UTF-8', 'es_ES', 'es', 'Spanish_Spain.1252', 'Spanish']
            configurado_es_cita = False
            for loc_cita in locales_a_intentar_es_cita:
                try:
                    locale.setlocale(locale.LC_TIME, loc_cita)
                    fecha_cita_str_buffer = proxima_cita_obj.fecha.strftime("%d %b")
                    configurado_es_cita = True
                    break
                except locale.Error:
                    continue
            if not configurado_es_cita:
                locale.setlocale(locale.LC_TIME, '')
                fecha_cita_str_buffer = proxima_cita_obj.fecha.strftime("%d %b")
        except Exception as e_cita_fecha:
            print(f"Error al formatear fecha_cita_str: {e_cita_fecha}")
            fecha_cita_str_buffer = proxima_cita_obj.fecha.strftime("%d %b") 
        finally:
            if locale_original_time != (None, None): 
                try:
                    locale.setlocale(locale.LC_TIME, locale_original_time)
                except locale.Error:
                    pass 
        
        hora_cita_str = proxima_cita_obj.hora.strftime("%I:%M %p")
        proxima_cita_data = {
            'fecha_formateada': f"{fecha_cita_str_buffer}, {hora_cita_str}",
            'paciente_nombre': f"{proxima_cita_obj.paciente.nombres} {proxima_cita_obj.paciente.apellidos}",
            'motivo': getattr(proxima_cita_obj, 'motivo', None) or "No especificado"
        }
    datos_panel['proxima_cita'] = proxima_cita_data

    # 4. Fecha actual corta (TU CÓDIGO ACTUAL - SIN CAMBIOS AQUÍ)
    fecha_corta_buffer = None
    # locale_original_time ya fue guardado
    try:
        locales_a_intentar_es_corta = ['es_ES.UTF-8', 'es_ES', 'es', 'Spanish_Spain.1252', 'Spanish']
        configurado_es_corta = False
        for loc_es_corta in locales_a_intentar_es_corta:
            try:
                locale.setlocale(locale.LC_TIME, loc_es_corta)
                fecha_corta_buffer = hoy.strftime("%d de %B").capitalize()
                configurado_es_corta = True
                break 
            except locale.Error:
                continue
        if not configurado_es_corta:
            locale.setlocale(locale.LC_TIME, '') 
            fecha_corta_buffer = hoy.strftime("%d de %B").capitalize()
    except Exception as e_corta:
        print(f"Error al formatear fecha_actual_corta: {e_corta}")
        fecha_corta_buffer = hoy.strftime("%d %B").capitalize() 
    finally:
        if locale_original_time != (None, None):
            try:
                locale.setlocale(locale.LC_TIME, locale_original_time)
            except locale.Error:
                pass 
    datos_panel['fecha_actual_corta'] = fecha_corta_buffer

    # 5. Lista de citas de hoy
    # Mostrar solo citas activas de pacientes activos
    citas_de_hoy_lista = Cita.query.options(joinedload(Cita.paciente))\
        .join(Paciente, Cita.paciente_id == Paciente.id)\
        .filter(
            Cita.fecha == hoy,
            Cita.is_deleted == False,         # <<<--- FILTRO AÑADIDO --- >>>
            Paciente.is_deleted == False      # <<<--- FILTRO AÑADIDO --- >>>
        )\
        .order_by(Cita.hora)\
        .all()
    
    citas_hoy_procesadas = []
    for cita_item in citas_de_hoy_lista:
        citas_hoy_procesadas.append({
            'id': cita_item.id,
            'hora_formateada': cita_item.hora.strftime("%I:%M %p"), 
            'paciente_nombre_completo': f"{cita_item.paciente.nombres} {cita_item.paciente.apellidos}",
            'motivo': getattr(cita_item, 'motivo', None) or "No especificado",
            'doctor': getattr(cita_item.paciente, 'doctor', getattr(cita_item, 'doctor', None)), # Tomar doctor del paciente si existe, sino de la cita
            'estado': getattr(cita_item, 'estado', 'pendiente')
        })
    datos_panel['citas_del_dia'] = citas_hoy_procesadas
    
    return datos_panel

def convertir_a_fecha(valor):
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None



        