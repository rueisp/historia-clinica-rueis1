# routes/calendario.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app # MODIFICACIÓN: Añadido current_app
from datetime import date, datetime, timedelta 
import calendar
from ..models import db, Cita, Paciente, AuditLog
from sqlalchemy.orm import joinedload
from sqlalchemy import extract, func, exc as sqlalchemy_exc
from urllib.parse import urlparse, urljoin 
import uuid 
import os
from shutil import copyfile
from flask_login import current_user, login_required
from uuid import uuid4 


calendario_bp = Blueprint('calendario', __name__, url_prefix='/calendario')

# --- Nombres de los meses (si no está global en app.py) ---
NOMBRES_MESES_ESP = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# --- Función de utilidad para URL segura (si no está global) ---
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

# --- Función para construir los días del mes ---
def construir_dias_del_mes(anio, mes, citas_del_mes_obj):
    dias_calendario = []
    primer_dia_obj = date(anio, mes, 1)
    total_dias_en_mes = calendar.monthrange(anio, mes)[1]
    dia_hoy = date.today()
    dia_semana_inicio = (primer_dia_obj.weekday() + 1) % 7  # Domingo como 0

    for _ in range(dia_semana_inicio):
        dias_calendario.append({'fecha': None, 'hoy': False, 'citas': []})

    for dia_num in range(1, total_dias_en_mes + 1):
        fecha_actual_dia = date(anio, mes, dia_num)
        citas_en_dia_actual = [c for c in citas_del_mes_obj if c.fecha == fecha_actual_dia]
        dias_calendario.append({
            'fecha': fecha_actual_dia,
            'hoy': fecha_actual_dia == dia_hoy,
            'citas': citas_en_dia_actual
        })

    total_celdas_actual = len(dias_calendario)
    celdas_vacias_final = (7 - total_celdas_actual % 7) % 7
    for _ in range(celdas_vacias_final):
        dias_calendario.append({'fecha': None, 'hoy': False, 'citas': []})
    return dias_calendario

# En routes/calendario.py

@calendario_bp.route('/') 
@login_required # Es fundamental proteger esta vista
def mostrar_calendario():
    anio_actual = request.args.get('anio', default=date.today().year, type=int)
    mes_actual = request.args.get('mes', default=date.today().month, type=int)

    try:
        date(anio_actual, mes_actual, 1)
    except ValueError:
        flash("Mes o año inválido.", "warning")
        anio_actual = date.today().year
        mes_actual = date.today().month

    # --- INICIO DE LA MODIFICACIÓN DE LA CONSULTA ---
    
    # 1. Construimos la consulta base con las condiciones que se aplican a TODOS
    query_citas = Cita.query.join(Paciente, Cita.paciente_id == Paciente.id).filter(
        Cita.is_deleted == False,
        Paciente.is_deleted == False,
        extract('year', Cita.fecha) == anio_actual,
        extract('month', Cita.fecha) == mes_actual
    )

    # 2. Si el usuario NO es un administrador, añadimos el filtro de propietario
    #    Esto asegura que solo vea las citas de SUS pacientes.
    if not current_user.is_admin:
        query_citas = query_citas.filter(Paciente.odontologo_id == current_user.id)
        
    # 3. Ejecutamos la consulta final con las optimizaciones y el ordenamiento
    citas_del_mes = query_citas.options(joinedload(Cita.paciente)).order_by(Cita.fecha, Cita.hora).all()

    # --- FIN DE LA MODIFICACIÓN ---

    # El resto de la función se mantiene exactamente igual
    dias_render = construir_dias_del_mes(anio_actual, mes_actual, citas_del_mes)
    nombre_mes_actual_display = NOMBRES_MESES_ESP[mes_actual-1]

    return render_template('calendario.html',
                           anio=anio_actual,
                           mes=mes_actual,
                           nombres_meses=NOMBRES_MESES_ESP,
                           nombre_mes_display=nombre_mes_actual_display,
                           dias=dias_render,
                           anio_hoy=date.today().year,
                           mes_hoy=date.today().month)
    

# --- VERSIÓN FINAL Y SIMPLIFICADA: registrar_cita ---
@calendario_bp.route('/registrar_cita', defaults={'paciente_id_param': None}, methods=['GET', 'POST'])
@calendario_bp.route('/registrar_cita/paciente/<int:paciente_id_param>', methods=['GET', 'POST'])
def registrar_cita(paciente_id_param):
    # (El código para GET y la inicialización de form_values se mantiene igual)
    next_url_get = request.args.get('next')
    fecha_preseleccionada_str = request.args.get('fecha') if request.method == 'GET' else None
    paciente_obj_preseleccionado = None

    if paciente_id_param:
        paciente_obj_preseleccionado = Paciente.query.filter_by(id=paciente_id_param, is_deleted=False).first()
        if not paciente_obj_preseleccionado:
            flash("Paciente preseleccionado no encontrado o está en la papelera.", "error")
            return redirect(next_url_get or url_for('.mostrar_calendario'))

    form_values = {
        'paciente_nombres_val': '', 'paciente_apellidos_val': '', 'paciente_edad_val': '',
        'paciente_documento_val': '', 'paciente_telefono_val': '',
        'fecha_val': fecha_preseleccionada_str or '', 'hora_val': '',
        'doctor_val': '', 'motivo_val': '', 'observaciones_val': '',
        'next_url': next_url_get or '',
        'paciente_preseleccionado_id': paciente_obj_preseleccionado.id if paciente_obj_preseleccionado else None,
        'paciente_preseleccionado_nombre': f"{paciente_obj_preseleccionado.nombres} {paciente_obj_preseleccionado.apellidos}" if paciente_obj_preseleccionado else None,
        'posibles_pacientes_encontrados': [],
        'mostrar_seccion_duplicados': False
    }

    if request.method == 'POST':
        # --- Recolección y validación de datos (sin cambios) ---
        current_next_url = request.form.get('next') or next_url_get or ''
        # ... (resto de la recolección de datos que ya tienes) ...
        nombres_pac_form = request.form.get('paciente_nombres', '').strip()
        apellidos_pac_form = request.form.get('paciente_apellidos', '').strip()
        edad_pac_str = request.form.get('paciente_edad', '').strip()
        documento_pac_form = request.form.get('paciente_documento', '').strip() or None
        telefono_pac_form = request.form.get('paciente_telefono', '').strip()
        fecha_str = request.form.get('fecha')
        hora_str = request.form.get('hora')
        doctor_form = request.form.get('doctor', '').strip()
        motivo_form = request.form.get('motivo', '').strip()
        observaciones_form = request.form.get('observaciones', '').strip()

        form_values.update({
            'paciente_nombres_val': nombres_pac_form, 'paciente_apellidos_val': apellidos_pac_form,
            'paciente_edad_val': edad_pac_str, 'paciente_documento_val': documento_pac_form,
            'paciente_telefono_val': telefono_pac_form,
            'fecha_val': fecha_str, 'hora_val': hora_str, 'doctor_val': doctor_form,
            'motivo_val': motivo_form, 'observaciones_val': observaciones_form
        })

        if not (fecha_str and hora_str and doctor_form):
            flash("La fecha, hora y doctor son campos obligatorios para la cita.", "error")
            return render_template('registrar_cita.html', form_values=form_values)
        try:
            fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            hora_obj = datetime.strptime(hora_str, "%H:%M").time()
        except ValueError:
            flash("Formato de fecha u hora inválido.", "error")
            return render_template('registrar_cita.html', form_values=form_values)
        
        paciente_para_la_cita = None
        paciente_fue_creado_ahora = False

        if paciente_obj_preseleccionado:
            paciente_para_la_cita = paciente_obj_preseleccionado
        elif request.form.get('paciente_id_seleccionado_duplicado'):
            paciente_id_elegido = request.form.get('paciente_id_seleccionado_duplicado', type=int)
            paciente_para_la_cita = Paciente.query.filter_by(id=paciente_id_elegido, is_deleted=False).first()
            if not paciente_para_la_cita:
                flash("El paciente seleccionado de la lista ya no es válido.", "error")
                return render_template('registrar_cita.html', form_values=form_values)
        else:
            if not (nombres_pac_form and apellidos_pac_form):
                flash("Los nombres y apellidos del paciente son obligatorios.", "error")
                return render_template('registrar_cita.html', form_values=form_values)
            if documento_pac_form:
                paciente_para_la_cita = Paciente.query.filter_by(documento=documento_pac_form, is_deleted=False).first()
            if not paciente_para_la_cita:
                # ... (lógica de buscar por nombre que ya tienes) ...
                # CÓDIGO CORREGIDO
                coincidencias_por_nombre = Paciente.query.filter(
                    func.lower(Paciente.nombres) == func.lower(nombres_pac_form),
                    func.lower(Paciente.apellidos) == func.lower(apellidos_pac_form),
                    Paciente.is_deleted == False
                ).all()
                if len(coincidencias_por_nombre) == 1:
                    paciente_para_la_cita = coincidencias_por_nombre[0]
                # --- CÓDIGO CORREGIDO ---
                elif len(coincidencias_por_nombre) > 1:
                    # Se encontraron varios, se detiene el proceso y se le pide al usuario que elija.
                    flash("Se encontraron varios pacientes con el mismo nombre. Por favor, seleccione el correcto o confirme la creación de uno nuevo.", "warning")
                    form_values['posibles_pacientes_encontrados'] = coincidencias_por_nombre
                    form_values['mostrar_seccion_duplicados'] = True
                    return render_template('registrar_cita.html', form_values=form_values)
                
            if not paciente_para_la_cita:
                # --- PUNTO DE INSERCIÓN DEL NUEVO CÓDIGO ---
                if documento_pac_form and Paciente.query.filter_by(documento=documento_pac_form, is_deleted=False).first():
                    flash(f"Error: Se intentó crear un nuevo paciente, pero el documento '{documento_pac_form}' ya pertenece a otro registro.", "danger")
                    return render_template('registrar_cita.html', form_values=form_values)
                if not telefono_pac_form:
                    flash("El teléfono es obligatorio para registrar un nuevo paciente.", "error")
                    return render_template('registrar_cita.html', form_values=form_values)
                
                edad_pac_actual = int(edad_pac_str) if edad_pac_str.isdigit() else None
                
                # --- INICIO DE LA LÓGICA DE COPIA DEL DENTIGRAMA AÑADIDA ---
                dentigrama_db_path = None
                try:
                    nombre_archivo_base = "dentigrama1.png" # <<<--- ¡VERIFICA ESTE NOMBRE!
                    ruta_origen_base_abs = os.path.join(current_app.static_folder, 'img', nombre_archivo_base)
                    
                    print(f"DEBUG: Intentando copiar desde: {ruta_origen_base_abs}")
                    if not os.path.exists(ruta_origen_base_abs):
                        raise FileNotFoundError(f"El archivo de dentigrama base no se encontró: {ruta_origen_base_abs}")

                    filename_dentigrama_paciente = f"{uuid4().hex}_{nombre_archivo_base}"
                    ruta_destino_copia_abs = os.path.join(current_app.config['UPLOAD_FOLDER_DENTIGRAMAS'], filename_dentigrama_paciente)
                    
                    with open(ruta_origen_base_abs, 'rb') as f_origen, open(ruta_destino_copia_abs, 'wb') as f_destino:
                        f_destino.write(f_origen.read())
                    
                    dentigrama_db_path = os.path.join("img", "pacientes", "dentigramas", filename_dentigrama_paciente).replace("\\", "/")
                    print(f"DEBUG (desde cita): ¡ÉXITO! Se creó el archivo de dentigrama en: {ruta_destino_copia_abs}")
                
                except Exception as e_copy:
                    flash("ADVERTENCIA: No se pudo asignar el dentigrama base al nuevo paciente.", "warning")
                    current_app.logger.error(f"Error CRÍTICO al copiar dentigrama base desde cita: {e_copy}", exc_info=True)
                    dentigrama_db_path = None
                # --- FIN DE LA LÓGICA DE COPIA ---

                paciente_para_la_cita = Paciente(
                    nombres=nombres_pac_form,
                    apellidos=apellidos_pac_form,
                    edad=edad_pac_actual,
                    documento=documento_pac_form,
                    telefono=telefono_pac_form,
                    odontologo=current_user,
                    dentigrama_url=dentigrama_url,
                )
                db.session.add(paciente_para_la_cita)
                paciente_fue_creado_ahora = True
                flash(f"Se creará un nuevo paciente: {nombres_pac_form} {apellidos_pac_form}.", "info")

                # ... (resto del código sin cambios) ...
        # ... código anterior ...

        # Esta condición ahora se evalúa DESPUÉS de haber buscado por documento Y por nombre
        if not paciente_para_la_cita: # <-- Tu línea 236
            # --- INICIO DEL BLOQUE INDENTADO ---
            
            # Todas estas líneas deben estar un nivel a la derecha
            if documento_pac_form and Paciente.query.filter_by(documento=documento_pac_form, is_deleted=False).first():
                flash(f"Error: Se intentó crear un nuevo paciente, pero el documento '{documento_pac_form}' ya pertenece a otro registro.", "danger")
                return render_template('registrar_cita.html', form_values=form_values)
            
            if not telefono_pac_form:
                flash("El teléfono es obligatorio para registrar un nuevo paciente.", "error")
                return render_template('registrar_cita.html', form_values=form_values)
            
            edad_pac_actual = int(edad_pac_str) if edad_pac_str.isdigit() else None
            
            # --- LÓGICA DE COPIA DEL DENTIGRAMA (también indentada) ---
            dentigrama_db_path = None
            try:
                nombre_archivo_base = "dentigrama1.png"
                ruta_origen_base_abs = os.path.join(current_app.static_folder, 'img', nombre_archivo_base)
                
                print(f"DEBUG: Intentando copiar desde: {ruta_origen_base_abs}")
                if not os.path.exists(ruta_origen_base_abs):
                    raise FileNotFoundError(f"El archivo de dentigrama base no se encontró: {ruta_origen_base_abs}")
                
                # ... (resto de la lógica de copia) ...
                
                dentigrama_db_path = os.path.join("img", "pacientes", "dentigramas", filename_dentigrama_paciente).replace("\\", "/")
                print(f"DEBUG (desde cita): ¡ÉXITO! Se creó el archivo de dentigrama en: {ruta_destino_copia_abs}")
            
            except Exception as e_copy:
                # ... (manejo de la excepción, también indentado) ...
                dentigrama_db_path = None
                
            # --- Creación del objeto Paciente (también indentada) ---
            paciente_para_la_cita = Paciente(
                nombres=nombres_pac_form,
                apellidos=apellidos_pac_form,
                edad=edad_pac_actual,
                documento=documento_pac_form,
                telefono=telefono_pac_form,
                odontologo=current_user,
                dentigrama_url=dentigrama_url,
            )
            
            db.session.add(paciente_para_la_cita)
            paciente_fue_creado_ahora = True
            flash(f"Se creará un nuevo paciente: {nombres_pac_form} {apellidos_pac_form}.", "info")

            # --- FIN DEL BLOQUE INDENTADO ---

        # Esta parte ya va fuera del if not paciente_para_la_cita
        if not paciente_para_la_cita:
            flash("No se pudo determinar el paciente para la cita. Por favor, intente de nuevo.", "danger")
            return render_template('registrar_cita.html', form_values=form_values)

        # ... (resto de la función) ...
            # ...
        
# ... código anterior ...

        # PASO 3: Crear la cita y guardar en la base de datos.
        try:
            # En este punto, `paciente_para_la_cita` es un objeto válido, ya sea existente o nuevo (y añadido a la sesión).
            nueva_cita = Cita(
                fecha=fecha_obj,
                hora=hora_obj,
                doctor=doctor_form,
                motivo=motivo_form or None,
                observaciones=observaciones_form or None,
                paciente=paciente_para_la_cita # Relación clave
            )
            db.session.add(nueva_cita)
            db.session.commit() # Esto guardará tanto el paciente nuevo (si lo hay) como la nueva cita.

            flash("Cita registrada correctamente.", "success")
            
            # Lógica de redirección
            redirect_url = form_values.get('next_url')
            if redirect_url and is_safe_url(redirect_url):
                return redirect(redirect_url)
            return redirect(url_for('.mostrar_calendario', anio=fecha_obj.year, mes=fecha_obj.month))

        except sqlalchemy_exc.IntegrityError as e_int:
            db.session.rollback()
            current_app.logger.error(f"Error de Integridad INESPERADO al guardar cita/paciente: {e_int}", exc_info=True)
            flash(f"Error al guardar: Hubo un conflicto de datos únicos en el último momento. Por favor, intente de nuevo.", "danger")
            return render_template('registrar_cita.html', form_values=form_values)

        # --- BLOQUE A CORREGIR ---
        except Exception as e: # <-- Tu línea 302
            # Este es el código indentado que faltaba
            db.session.rollback()
            flash(f"Ocurrió un error inesperado al guardar la cita: {str(e)}", "error")
            current_app.logger.error(f"Error detallado al guardar cita: {e}", exc_info=True)
            return render_template('registrar_cita.html', form_values=form_values)
        # --- FIN DE LA CORRECCIÓN ---
    return render_template('registrar_cita.html', form_values=form_values)

# --- MODIFICADA: editar_cita ---
@calendario_bp.route('/editar_cita/<int:cita_id>', methods=['GET', 'POST'])
def editar_cita(cita_id):
    cita_obj = Cita.query.options(joinedload(Cita.paciente)).get_or_404(cita_id)

    if not current_user.is_admin and cita_obj.paciente.odontologo_id != current_user.id:
        flash("Acceso denegado. No tienes permiso para editar esta cita.", "danger")
        return redirect(url_for('.mostrar_calendario')) # Usamos .mostrar_calendario porque estamos en el mismo blueprint

    pacientes_para_dropdown_query = Paciente.query.filter_by(is_deleted=False)
    if not current_user.is_admin:
        pacientes_para_dropdown_query = pacientes_para_dropdown_query.filter_by(odontologo_id=current_user.id)
    
    todos_los_pacientes = pacientes_para_dropdown_query.order_by(Paciente.apellidos, Paciente.nombres).all()

    
    next_url_get = request.args.get('next')
    
    todos_los_pacientes = Paciente.query.order_by(Paciente.apellidos, Paciente.nombres).all()

    form_data_edit = {
        'selected_paciente_id': str(cita_obj.paciente_id), 
        'fecha_val': cita_obj.fecha.strftime('%Y-%m-%d'),
        'hora_val': cita_obj.hora.strftime('%H:%M'),
        'doctor_val': cita_obj.doctor,
        'motivo_val': cita_obj.motivo or '',
        'observaciones_val': cita_obj.observaciones or '',
        'next_url': next_url_get
    }

    if request.method == 'POST':
        current_next_url = request.form.get('next') or next_url_get
        form_data_edit['next_url'] = current_next_url 

        paciente_id_form = request.form.get('paciente_id', type=int)
        fecha_str = request.form.get('fecha')
        hora_str = request.form.get('hora')
        doctor_form = request.form.get('doctor')
        motivo_form = request.form.get('motivo')
        observaciones_form = request.form.get('observaciones')
        
                # --- VERIFICACIÓN DE SEGURIDAD ADICIONAL EN POST ---
        # 4. Asegurarse de que el paciente al que se asigna la cita también
        #    pertenece al doctor (o que el usuario es admin).
        if not current_user.is_admin:
            paciente_destino = Paciente.query.filter_by(id=paciente_id_form, odontologo_id=current_user.id).first()
            if not paciente_destino:
                flash("Error: Se intentó asignar la cita a un paciente que no te pertenece.", "danger")
                return render_template('editar_cita.html', cita=cita_obj, pacientes=todos_los_pacientes, form_data=form_data_edit)
        # --- FIN VERIFICACIÓN POST ---
        
        

        form_data_edit.update({
            'selected_paciente_id': paciente_id_form, 'fecha_val': fecha_str, 'hora_val': hora_str,
            'doctor_val': doctor_form, 'motivo_val': motivo_form, 'observaciones_val': observaciones_form
        })

        if not (paciente_id_form and fecha_str and hora_str and doctor_form):
            flash("Paciente, fecha, hora y doctor son campos obligatorios.", "error")
            return render_template('editar_cita.html', cita=cita_obj, pacientes=todos_los_pacientes, form_data=form_data_edit)

        try:
            cita_obj.paciente_id = int(paciente_id_form)
            cita_obj.fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            cita_obj.hora = datetime.strptime(hora_str, "%H:%M").time()
        except ValueError:
            flash("Formato de ID de paciente, fecha u hora inválido.", "error")
            return render_template('editar_cita.html', cita=cita_obj, pacientes=todos_los_pacientes, form_data=form_data_edit)

        cita_obj.doctor = doctor_form
        cita_obj.motivo = motivo_form or None
        cita_obj.observaciones = observaciones_form or None

        try:
            db.session.commit()
            flash("Cita actualizada correctamente.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar la cita: {e}", "error")
            current_app.logger.error(f"Error detallado al editar cita: {e}", exc_info=True) # MODIFICACIÓN: Añadido exc_info=True
            return render_template('editar_cita.html', cita=cita_obj, pacientes=todos_los_pacientes, form_data=form_data_edit)

        if form_data_edit['next_url'] and is_safe_url(form_data_edit['next_url']):
            return redirect(form_data_edit['next_url'])
        return redirect(url_for('.mostrar_calendario', anio=cita_obj.fecha.year, mes=cita_obj.fecha.month))

    return render_template('editar_cita.html', cita=cita_obj, pacientes=todos_los_pacientes, form_data=form_data_edit)


# --- MODIFICADA: eliminar_cita con Auditoría ---

@calendario_bp.route('/eliminar_cita/<int:cita_id>', methods=['POST'])
@login_required # Buena práctica proteger acciones de eliminación
def eliminar_cita(cita_id):
    # Cargar la cita y el paciente asociado para tener información completa para el log
    cita_a_mover_papelera = Cita.query.options(joinedload(Cita.paciente)).get_or_404(cita_id)
    
    if not current_user.is_admin and cita_a_mover_papelera.paciente.odontologo_id != current_user.id:
        flash("Acceso denegado. No tienes permiso para eliminar esta cita.", "danger")
        return redirect(url_for('.mostrar_calendario'))
    
    if cita_a_mover_papelera.is_deleted:
        flash('Esta cita ya se encuentra en la papelera.', 'info')
        # Redirigir a donde sea apropiado, quizás a la vista del paciente o al calendario
        next_url_fallback = url_for('.mostrar_calendario', 
                                    anio=cita_a_mover_papelera.fecha.year, 
                                    mes=cita_a_mover_papelera.fecha.month)
        if cita_a_mover_papelera.paciente_id:
            # Ajusta 'pacientes.mostrar_paciente' al nombre correcto de tu blueprint/ruta
            next_url_fallback = url_for('pacientes.mostrar_paciente', id=cita_a_mover_papelera.paciente_id) 
        return redirect(request.form.get('next') or next_url_fallback)

    # Guardar información para el log ANTES de modificar el objeto cita
    paciente_nombre_log = "Desconocido"
    if cita_a_mover_papelera.paciente: 
        paciente_nombre_log = f"{cita_a_mover_papelera.paciente.nombres} {cita_a_mover_papelera.paciente.apellidos}"
    
    log_descripcion_detalle = (
        f"Cita (ID: {cita_a_mover_papelera.id}) "
        f"para el paciente '{paciente_nombre_log}' (Paciente ID: {cita_a_mover_papelera.paciente_id}) "
        f"del {cita_a_mover_papelera.fecha.strftime('%d/%m/%Y')} a las {cita_a_mover_papelera.hora.strftime('%H:%M')} "
        f"con Dr(a). {cita_a_mover_papelera.doctor or 'N/A'}. Motivo: {cita_a_mover_papelera.motivo or 'No especificado'}."
    )
    cita_id_para_log = cita_a_mover_papelera.id
    
    next_url = request.form.get('next') 
    # Guardar el año y mes para la redirección de fallback ANTES de cualquier commit, 
    # ya que el objeto podría desvincularse si la sesión expira.
    anio_cita_fallback = cita_a_mover_papelera.fecha.year
    mes_cita_fallback = cita_a_mover_papelera.fecha.month
    paciente_id_fallback = cita_a_mover_papelera.paciente_id


    try:
        # --- SOFT DELETE CITA ---
        cita_a_mover_papelera.is_deleted = True
        cita_a_mover_papelera.deleted_at = datetime.utcnow()
        # --- FIN SOFT DELETE CITA ---

        # Crear el registro de auditoría
        audit_entry = AuditLog(
            action_type="SOFT_DELETE_CITA", # Nuevo tipo de acción
            description=f"Cita movida a la papelera: {log_descripcion_detalle}",
            target_model="Cita",
            target_id=cita_id_para_log,
            # Opcional: related_target_model="Paciente", related_target_id=cita_a_mover_papelera.paciente_id
        )
        
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            audit_entry.user_id = current_user.id
            audit_entry.user_username = current_user.username 
        else:
            audit_entry.user_username = "Sistema/Desconocido"

        db.session.add(audit_entry) 
        # NO db.session.delete(cita_a_mover_papelera)
        
        db.session.commit() 
        
        flash("Cita movida a la papelera y acción registrada.", "success")

    except Exception as e:
        db.session.rollback() 
        flash(f"Error al mover la cita a la papelera: {str(e)}", "error")
        current_app.logger.error(f"Error detallado al mover cita ID {cita_id} a la papelera o registrar auditoría: {e}", exc_info=True)

    # Lógica de redirección
    if next_url and is_safe_url(next_url):
        return redirect(next_url)
    
    # Fallback a la vista del paciente si existe, sino al calendario
    if paciente_id_fallback:
        try:
            # AJUSTA 'pacientes.mostrar_paciente' al nombre de tu blueprint de pacientes y la ruta
            return redirect(url_for('pacientes.mostrar_paciente', id=paciente_id_fallback))
        except Exception: # BuildError si la ruta no existe o el blueprint no está bien nombrado
            current_app.logger.warning(f"No se pudo redirigir a la vista del paciente {paciente_id_fallback}, yendo al calendario.")
            pass # Continuar al fallback del calendario
            
    return redirect(url_for('.mostrar_calendario', anio=anio_cita_fallback, mes=mes_cita_fallback))


# --- NUEVA RUTA: Actualizar Estado de la Cita ---
@calendario_bp.route('/cita/actualizar_estado/<int:cita_id>', methods=['POST'])
def actualizar_estado_cita(cita_id):
    cita = Cita.query.get(cita_id)

    if not cita:
        return jsonify({'success': False, 'message': 'Cita no encontrada.'}), 404

    data = request.get_json()
    if not data or 'estado' not in data:
        return jsonify({'success': False, 'message': 'No se proporcionó el nuevo estado.'}), 400

    nuevo_estado = data.get('estado')
    estados_validos = ['pendiente', 'completada', 'cancelada', 'confirmada', 'reprogramada', 'no_asistio'] # MODIFICACIÓN: Ampliar estados si es necesario

    if nuevo_estado not in estados_validos:
        return jsonify({'success': False, 'message': f"Estado '{nuevo_estado}' no válido."}), 400

    try:
        cita.estado = nuevo_estado
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Estado de la cita actualizado correctamente.',
            'nuevo_estado': nuevo_estado, 
            'cita_id': cita_id
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al actualizar estado de cita ID {cita_id} a '{nuevo_estado}': {e}", exc_info=True) # MODIFICACIÓN: Añadido exc_info=True
        return jsonify({'success': False, 'message': 'Ocurrió un error al actualizar el estado de la cita.'}), 500