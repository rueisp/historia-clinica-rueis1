
import os
import base64
from uuid import uuid4
from datetime import date, datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, func, case
from ..extensions import db
from ..models import Paciente, Cita, Evolucion, AuditLog
from ..utils import allowed_file, convertir_a_fecha, eliminar_imagen

pacientes_bp = Blueprint('pacientes', __name__, url_prefix='/pacientes') # Añadí url_prefix por consistencia




@pacientes_bp.route('/')
@login_required
def lista_pacientes():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('buscar', '').strip()

    # 1. Empieza con la consulta base (solo pacientes no borrados)
    query = Paciente.query.filter(Paciente.is_deleted == False)

    if not current_user.is_admin:
        query = query.filter(Paciente.odontologo_id == current_user.id)

    if search_term:
        query = query.filter(
            or_(
                Paciente.nombres.ilike(f"%{search_term}%"),
                Paciente.apellidos.ilike(f"%{search_term}%"),
                Paciente.documento.ilike(f"%{search_term}%")
            )
        )
    
    pacientes = query.order_by(Paciente.apellidos, Paciente.nombres).paginate(
        page=page, per_page=7, error_out=False
    )
    
    print(f"Usuario: {current_user.username}, es admin: {current_user.is_admin}")
    print(f"Pacientes encontrados para este usuario: {pacientes.total}")

    return render_template('pacientes.html', pacientes=pacientes, buscar=search_term)


@pacientes_bp.route('/<int:id>', methods=['GET', 'POST']) # Cambiado a una URL más RESTful
@login_required # 1. Proteger la ruta, es fundamental
def mostrar_paciente(id):

    query = Paciente.query.filter_by(id=id, is_deleted=False)
    
    if not current_user.is_admin:
        query = query.filter_by(odontologo_id=current_user.id)
        
    paciente = query.first_or_404()
    
    if request.method == 'POST':
        # Corrección 1: Usar .get() con paréntesis, no con corchetes.
        descripcion = request.form.get('descripcion')
        
        if descripcion and descripcion.strip():
            nueva_evolucion = Evolucion(
                descripcion=descripcion.strip(),
                paciente_id=paciente.id # Usamos el id del paciente seguro que ya obtuvimos
                # La fecha se puede añadir por defecto en el modelo para más limpieza
            )
            db.session.add(nueva_evolucion)
            db.session.commit()
            flash('Evolución añadida correctamente.', 'success')
        else:
            flash('La descripción de la evolución no puede estar vacía.', 'warning')

        return redirect(url_for('pacientes.mostrar_paciente', id=paciente.id))

    return render_template('mostrar_paciente.html', paciente=paciente)


# --- RUTA UNIFICADA PARA CREAR PACIENTES ---
@pacientes_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_paciente():
    if request.method == 'POST':
        
        documento = request.form.get('documento')
        if not documento:
            flash('El número de documento es obligatorio.', 'danger')
            return render_template('registrar_paciente.html', form_data=request.form)

        paciente_existente = Paciente.query.filter_by(documento=documento).first()
        if paciente_existente:
            flash(f'Ya existe un paciente registrado con el documento {documento}.', 'danger')
            return render_template('registrar_paciente.html', form_data=request.form)

        # Si llegamos aquí, el documento es válido y podemos proceder.
        
        try:

            # Usar las rutas absolutas de app.config para el destino de guardado
            carpeta_destino_imagenes_abs = current_app.config['UPLOAD_FOLDER_IMAGENES']
            carpeta_destino_dentigrama_abs = current_app.config['UPLOAD_FOLDER_DENTIGRAMAS']
            os.makedirs(carpeta_destino_imagenes_abs, exist_ok=True)
            os.makedirs(carpeta_destino_dentigrama_abs, exist_ok=True) # Esta ya usaba app.config indirectamente

            # --- CAMBIO FIN ---

            # Obtener datos del formulario (sin cambios aquí)
            nombres = request.form.get('nombres')
            apellidos = request.form.get('apellidos')
            # ... (resto de tus request.form.get)
            tipo_documento = request.form.get('tipo_documento')
            documento = request.form.get('documento')
            fecha_nacimiento_str = request.form['fecha_nacimiento']
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date() if fecha_nacimiento_str else None    
            edad = int(request.form.get('edad')) if request.form.get('edad') else None
            email = request.form.get('email')
            telefono = request.form.get('telefono')
            genero = request.form.get('genero')
            estado_civil = request.form.get('estado_civil')
            direccion = request.form.get('direccion')
            barrio = request.form.get('barrio')
            municipio = request.form.get('municipio')
            departamento = request.form.get('departamento')
            aseguradora = request.form.get('aseguradora')
            tipo_vinculacion = request.form.get('tipo_vinculacion')
            ocupacion = request.form.get('ocupacion')
            referido_por = request.form.get('referido_por')
            nombre_responsable = request.form.get('nombre_responsable')
            telefono_responsable = request.form.get('telefono_responsable')
            parentesco = request.form.get('parentesco')
            motivo_consulta = request.form.get('motivo_consulta')
            enfermedad_actual = request.form.get('enfermedad_actual')
            antecedentes_personales = request.form.get('antecedentes_personales')
            antecedentes_familiares = request.form.get('antecedentes_familiares')
            antecedentes_quirurgicos = request.form.get('antecedentes_quirurgicos')
            antecedentes_hemorragicos = request.form.get('antecedentes_hemorragicos')
            farmacologicos = request.form.get('farmacologicos')
            reaccion_medicamentos = request.form.get('reaccion_medicamentos')
            alergias = request.form.get('alergias')
            habitos = request.form.get('habitos')
            cepillado = request.form.get('cepillado')
            examen_fisico = request.form.get('examen_fisico')
            ultima_visita_odontologo = request.form.get('ultima_visita_odontologo', '')
            plan_tratamiento = request.form.get('plan_tratamiento')
            observaciones = request.form.get('observaciones', '')  # Nuevo campo de observaciones
            imagen_1_file = request.files.get('imagen_1') # Renombrado para claridad
            imagen_2_file = request.files.get('imagen_2') # Renombrado para claridad
            
            # Rutas RELATIVAS para la base de datos (se almacenarán así)
            imagen_1_db_path = None
            imagen_2_db_path = None
            dentigrama_db_path = None

            # Validar si los archivos son de un tipo permitido
            if imagen_1_file and allowed_file(imagen_1_file.filename):
                filename_imagen_1 = secure_filename(f"{uuid4().hex}_{imagen_1_file.filename}")
                # --- CAMBIO ---
                # Ruta ABSOLUTA para guardar el archivo
                ruta_guardado_abs_imagen_1 = os.path.join(carpeta_destino_imagenes_abs, filename_imagen_1)
                imagen_1_file.save(ruta_guardado_abs_imagen_1)
                # Ruta RELATIVA para la DB (sin 'static/' y con separadores /)
                imagen_1_db_path = os.path.join("img", "pacientes", "imagenes", filename_imagen_1).replace("\\", "/")

            if imagen_2_file and allowed_file(imagen_2_file.filename):
                filename_imagen_2 = secure_filename(f"{uuid4().hex}_{imagen_2_file.filename}")
                # --- CAMBIO ---
                # Ruta ABSOLUTA para guardar el archivo
                ruta_guardado_abs_imagen_2 = os.path.join(carpeta_destino_imagenes_abs, filename_imagen_2)
                imagen_2_file.save(ruta_guardado_abs_imagen_2)
                # Ruta RELATIVA para la DB (sin 'static/' y con separadores /)
                imagen_2_db_path = os.path.join("img", "pacientes", "imagenes", filename_imagen_2).replace("\\", "/")

            # --- CÓDIGO CORREGIDO Y MEJORADO ---

            data_url = request.form.get('dentigrama_canvas')
            dentigrama_db_path = None  # Inicializamos como None

            if data_url and data_url.startswith("data:image"):
                # CASO 1: El usuario dibujó en el canvas y envió los datos.
                try:
                    filename_canvas = secure_filename(f"{uuid4().hex}_dentigrama_canvas.png")
                    ruta_guardado_abs_dentigrama = os.path.join(current_app.config['UPLOAD_FOLDER_DENTIGRAMAS'], filename_canvas)

                    header, encoded = data_url.split(",", 1)
                    with open(ruta_guardado_abs_dentigrama, "wb") as f:
                        f.write(base64.b64decode(encoded))

                    # Asignamos la ruta relativa para la base de datos
                    dentigrama_db_path = os.path.join("img", "pacientes", "dentigramas", filename_canvas).replace("\\", "/")
                    print(f"DEBUG: Guardado dentigrama desde canvas: {dentigrama_db_path}")

                except Exception as e_dent:
                    flash(f"ADVERTENCIA: Hubo un error al procesar el dentigrama enviado. El paciente se creará sin él. Error: {e_dent}", 'warning')
                    current_app.logger.error(f"Error procesando canvas para nuevo paciente: {e_dent}", exc_info=True)
                    dentigrama_db_path = None # Aseguramos que sea None si falla

            else:
                # CASO 2: El formulario no envió datos del canvas. Creamos una copia del dentigrama base.
                try:
                    # Define el nombre de tu archivo de dentigrama base
                    nombre_archivo_base = "dentigrama1.png" # <<<--- ¡ASEGÚRATE DE QUE ESTE NOMBRE ES CORRECTO!

                    # Ruta de origen (el archivo que quieres copiar)
                    ruta_origen_base_abs = os.path.join(current_app.static_folder, 'img', nombre_archivo_base)

                    # Nombre único para el archivo de destino del nuevo paciente
                    filename_dentigrama_paciente = f"{uuid4().hex}_{nombre_archivo_base}"
                    
                    # Ruta de destino (dónde se guardará la copia)
                    ruta_destino_copia_abs = os.path.join(current_app.config['UPLOAD_FOLDER_DENTIGRAMAS'], filename_dentigrama_paciente)

                    # Realizar la copia del archivo
                    # (Asegúrate de tener 'import shutil' al principio del archivo para la versión más robusta)
                    # shutil.copyfile(ruta_origen_base_abs, ruta_destino_copia_abs)
                    # O la versión sin importar shutil:
                    with open(ruta_origen_base_abs, 'rb') as f_origen, open(ruta_destino_copia_abs, 'wb') as f_destino:
                        f_destino.write(f_origen.read())
                    
                    # La ruta RELATIVA que se guardará en la base de datos
                    dentigrama_db_path = os.path.join("img", "pacientes", "dentigramas", filename_dentigrama_paciente).replace("\\", "/")
                    print(f"DEBUG: Creado dentigrama base para nuevo paciente: {dentigrama_db_path}")

                except FileNotFoundError:
                    flash(f"ADVERTENCIA: No se encontró el archivo de dentigrama base '{nombre_archivo_base}'. El paciente se creó sin dentigrama.", "warning")
                    current_app.logger.warning(f"No se encontró el archivo de dentigrama base en: {ruta_origen_base_abs}")
                    dentigrama_db_path = None # Aseguramos que sea None si falla la copia
                except Exception as e_copy:
                    flash(f"ADVERTENCIA: Ocurrió un error al asignar el dentigrama base. El paciente se creará sin él. Error: {e_copy}", "warning")
                    current_app.logger.error(f"Error copiando dentigrama base: {e_copy}", exc_info=True)
                    dentigrama_db_path = None # Aseguramos que sea None si falla la copia

            # Crear objeto Paciente con las rutas RELATIVAS para la DB
            nuevo_paciente = Paciente(
                nombres=nombres,
                apellidos=apellidos,
                tipo_documento=tipo_documento,
                documento=documento,
                fecha_nacimiento=fecha_nacimiento,
                telefono=telefono,
                edad=edad,
                email=email,
                genero=genero,
                estado_civil=estado_civil,
                direccion=direccion,
                barrio=barrio,
                municipio=municipio,
                departamento=departamento,
                aseguradora=aseguradora,
                tipo_vinculacion=tipo_vinculacion,
                ocupacion=ocupacion,
                referido_por=referido_por,
                nombre_responsable=nombre_responsable,
                telefono_responsable=telefono_responsable,
                parentesco=parentesco,
                motivo_consulta=motivo_consulta,
                enfermedad_actual=enfermedad_actual,
                antecedentes_personales=antecedentes_personales,
                antecedentes_familiares=antecedentes_familiares,
                antecedentes_quirurgicos=antecedentes_quirurgicos,
                antecedentes_hemorragicos=antecedentes_hemorragicos,
                farmacologicos=farmacologicos,
                reaccion_medicamentos=reaccion_medicamentos,
                alergias=alergias,
                habitos=habitos,
                cepillado=cepillado,
                examen_fisico=examen_fisico,
                ultima_visita_odontologo=ultima_visita_odontologo,
                plan_tratamiento=plan_tratamiento,
                observaciones=observaciones,  # Añadido el nuevo campo de observaciones
                imagen_1=imagen_1_db_path,
                imagen_2=imagen_2_db_path,
                dentigrama_canvas=dentigrama_db_path,
                odontologo_id=current_user.id
            )

            db.session.add(nuevo_paciente)
            db.session.commit()

            flash('Paciente guardado con éxito', 'success') # Cambiado a 'success' para consistencia
            return redirect(url_for('pacientes.lista_pacientes'))

        except Exception as e:
            db.session.rollback()
            # Mostramos un error genérico al usuario
            flash('Ocurrió un error inesperado al guardar el paciente. Por favor, revisa los datos.', 'danger')
            # Registramos el error real en los logs para que tú puedas verlo
            current_app.logger.error(f'Error al guardar paciente: {e}', exc_info=True)
            # Volvemos a mostrar el formulario, pasando los datos para no perderlos
            return render_template('registrar_paciente.html', form_data=request.form)

    return render_template('registrar_paciente.html', form_data={})   

# URL más limpia: /pacientes/123/borrar
@pacientes_bp.route('/<int:id>/borrar', methods=['POST']) 
@login_required
def borrar_paciente(id):
    
    query = Paciente.query.filter_by(id=id)

    if not current_user.is_admin:
        query = query.filter_by(odontologo_id=current_user.id)
        
    # 3. Obtener el paciente o devolver 404 (nuestro guardián de seguridad)
    paciente = query.first_or_404()
    
    # --- El resto de tu lógica de soft-delete está bien ---
    if paciente.is_deleted:
        flash(f"El paciente '{paciente.nombres} {paciente.apellidos}' ya se encuentra en la papelera.", 'info')
        return redirect(url_for('pacientes.lista_pacientes'))

    paciente_nombre_completo_para_log = f"{paciente.nombres} {paciente.apellidos}"
    
    try:
        paciente.is_deleted = True
        paciente.deleted_at = datetime.utcnow()

        # Soft delete en cascada para las citas
        citas_del_paciente = Cita.query.filter_by(paciente_id=paciente.id, is_deleted=False).all()
        for cita_item in citas_del_paciente:
            cita_item.is_deleted = True
            cita_item.deleted_at = datetime.utcnow()

        # Crear el log de auditoría
        log_descripcion = f"Paciente '{paciente_nombre_completo_para_log}' movido a la papelera."
        if citas_del_paciente:
            log_descripcion += f" También se movieron {len(citas_del_paciente)} cita(s) asociadas."
            
        audit_entry = AuditLog(
            action_type="SOFT_DELETE_PACIENTE",
            description=log_descripcion,
            target_model="Paciente",
            target_id=paciente.id,
            user_id=current_user.id,
            user_username=current_user.username
        )
        db.session.add(audit_entry)
        
        db.session.commit() 
        
        flash(f"Paciente '{paciente_nombre_completo_para_log}' movido a la papelera.", 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al mover paciente ID {id} a la papelera: {str(e)}", exc_info=True)
        flash('Ocurrió un error al mover el paciente a la papelera.', 'danger')
        
    return redirect(url_for('pacientes.lista_pacientes'))


@pacientes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_paciente(id):
    query = Paciente.query.filter_by(id=id, is_deleted=False)

    if not current_user.is_admin:
        query = query.filter_by(odontologo_id=current_user.id)
        
    paciente = query.first_or_404()
    
    if request.method == 'POST':
        try:
            print("Formulario enviado correctamente")

            # Datos personales
            paciente.nombres = request.form.get('nombres')
            paciente.apellidos = request.form.get('apellidos')
            paciente.tipo_documento = request.form.get('tipo_documento')
            documento_form = request.form.get('documento', '').strip()

            if documento_form:  # Si el usuario escribió algo en el campo de documento
                # Comprobar solo si el documento del formulario es DIFERENTE al que ya tiene el paciente
                if documento_form != paciente.documento:
                    # Verificar si este NUEVO documento ya lo tiene OTRO paciente
                    otro_paciente_con_doc = Paciente.query.filter(
                        Paciente.documento == documento_form,
                        Paciente.id != paciente.id
                    ).first()

                    if otro_paciente_con_doc:
                        # Si ya existe, mostrar un error y NO actualizar el documento
                        flash(f"Error: El documento '{documento_form}' ya está en uso por otro paciente.", "danger")
                    else:
                        # Si no existe, actualizar el documento del paciente actual
                        paciente.documento = documento_form
                # Si el documento no cambió, no hacemos nada.
            else:  # Si el campo del formulario se dejó vacío
                # Asignar None (que se convierte en NULL) solo si no hay ya otro paciente con documento NULL
                otro_paciente_sin_doc = Paciente.query.filter(
                    Paciente.documento.is_(None), # .is_(None) es la forma correcta de buscar NULL en SQLAlchemy
                    Paciente.id != paciente.id
                ).first()
                
                if otro_paciente_sin_doc:
                    # Si ya hay otro paciente sin documento, no podemos dejar este también sin documento.
                    # Informamos al usuario y NO cambiamos el documento actual.
                    # Esto solo ocurre si el paciente actual SÍ tenía un documento antes.
                    if paciente.documento is not None:
                        flash("Error: No se puede quitar el documento, ya que existe otro paciente sin documento asignado.", "warning")
                else:
                    # Es seguro asignar None porque no hay conflictos
                    paciente.documento = None

            # --- FIN DEL BLOQUE DE REEMPLAZO ---

    
            paciente.fecha_nacimiento = convertir_a_fecha(request.form.get('fecha_nacimiento', ''))
            edad_str = request.form.get('edad')
            if edad_str and edad_str.strip(): # Si hay algo y no son solo espacios
                try:
                    paciente.edad = int(edad_str)
                except ValueError:
                    # Si no se puede convertir a int, muestra un aviso y no actualiza la edad
                    flash('El valor ingresado para la edad no es un número válido. No se actualizó la edad.', 'warning')
                    # paciente.edad se mantendrá con su valor anterior si la conversión falla
            else:
                # Si el campo está vacío en el formulario, asigna None para que sea NULL en la DB
                paciente.edad = None
            # --- FIN DEL CAMBIO PARA EDAD ---

            # --- MANEJO INTELIGENTE DEL EMAIL (OPCIONAL) ---

            email_form = request.form.get('email', '').strip()

            # 2. Decidir qué hacer con el valor.
            if email_form:  # Si el usuario escribió algo en el campo...

                if email_form.lower() != (paciente.email.lower() if paciente.email else None):
                    otro_paciente_con_email = Paciente.query.filter(
                        func.lower(Paciente.email) == func.lower(email_form),
                        Paciente.id != paciente.id
                    ).first()

                    if otro_paciente_con_email:
                        flash(f"Error: El correo electrónico '{email_form}' ya está en uso por otro paciente.", "danger")
                        # NO actualizamos el email, dejamos el que ya tenía.
                    else:
                        # El email es nuevo y único, lo actualizamos.
                        paciente.email = email_form
                # Si el email no cambió, no hacemos nada.
            
            else:  # Si el campo email se dejó vacío...
                # 3. Guardar None (que se convertirá en NULL en la base de datos).
                paciente.email = None
            
            # --- FIN MANEJO DEL EMAIL ---

            paciente.genero = request.form.get('genero')
            paciente.estado_civil = request.form.get('estado_civil')
            paciente.direccion = request.form.get('direccion')
            paciente.barrio = request.form.get('barrio')
            paciente.municipio = request.form.get('municipio')
            paciente.departamento = request.form.get('departamento')
            paciente.aseguradora = request.form.get('aseguradora')
            paciente.tipo_vinculacion = request.form.get('tipo_vinculacion')
            paciente.ocupacion = request.form.get('ocupacion')
            paciente.referido_por = request.form.get('referido_por')

            # Datos del responsable
            paciente.nombre_responsable = request.form.get('nombre_responsable')
            paciente.telefono_responsable = request.form.get('telefono_responsable')
            paciente.parentesco = request.form.get('parentesco')

            # Antecedentes personales
            paciente.motivo_consulta = request.form.get('motivo_consulta')
            paciente.enfermedad_actual = request.form.get('enfermedad_actual')
            paciente.antecedentes_personales = request.form.get('antecedentes_personales')
            paciente.antecedentes_familiares = request.form.get('antecedentes_familiares')
            paciente.antecedentes_quirurgicos = request.form.get('antecedentes_quirurgicos')
            paciente.antecedentes_hemorragicos = request.form.get('antecedentes_hemorragicos')
            paciente.farmacologicos = request.form.get('farmacologicos')
            paciente.reaccion_medicamentos = request.form.get('reaccion_medicamentos')
            paciente.alergias = request.form.get('alergias')
            paciente.habitos = request.form.get('habitos')
            paciente.cepillado = request.form.get('cepillado')
            paciente.examen_fisico = request.form.get('examen_fisico')
            paciente.ultima_visita_odontologo = request.form.get('ultima_visita_odontologo')
            paciente.plan_tratamiento = request.form.get('plan_tratamiento')
            paciente.observaciones = request.form.get('observaciones')


            carpeta_destino_imagenes_abs = current_app.config['UPLOAD_FOLDER_IMAGENES']
            carpeta_destino_dentigrama_abs = current_app.config['UPLOAD_FOLDER_DENTIGRAMAS']

            os.makedirs(carpeta_destino_imagenes_abs, exist_ok=True)
            os.makedirs(carpeta_destino_dentigrama_abs, exist_ok=True)

            imagen_1_file = request.files.get('imagen_1')
            imagen_2_file = request.files.get('imagen_2')

            # Guardar imágenes en el modelo Paciente
            if imagen_1_file and allowed_file(imagen_1_file.filename):
                # Eliminar imagen anterior si existe y se está subiendo una nueva
                if paciente.imagen_1:
                    eliminar_imagen(paciente.imagen_1) # Asumo que esta función usa la ruta relativa a 'static'

                filename_imagen_1 = secure_filename(f"{uuid4().hex}_{imagen_1_file.filename}")
                ruta_guardado_abs_imagen_1 = os.path.join(carpeta_destino_imagenes_abs, filename_imagen_1)
                imagen_1_file.save(ruta_guardado_abs_imagen_1)
                paciente.imagen_1 = os.path.join('img', 'pacientes', 'imagenes', filename_imagen_1).replace("\\", "/")

            if imagen_2_file and allowed_file(imagen_2_file.filename):
                # Eliminar imagen anterior si existe y se está subiendo una nueva
                if paciente.imagen_2:
                    eliminar_imagen(paciente.imagen_2)

                filename_imagen_2 = secure_filename(f"{uuid4().hex}_{imagen_2_file.filename}")
                ruta_guardado_abs_imagen_2 = os.path.join(carpeta_destino_imagenes_abs, filename_imagen_2)
                imagen_2_file.save(ruta_guardado_abs_imagen_2)
                paciente.imagen_2 = os.path.join('img', 'pacientes', 'imagenes', filename_imagen_2).replace("\\", "/")

            # Eliminar imagen_1 si se marcó el checkbox y no se subió una nueva
            if request.form.get('eliminar_imagen_1') and paciente.imagen_1 and not imagen_1_file:
                eliminar_imagen(paciente.imagen_1)
                paciente.imagen_1 = None

            # Eliminar imagen_2 si se marcó el checkbox y no se subió una nueva
            if request.form.get('eliminar_imagen_2') and paciente.imagen_2 and not imagen_2_file:
                eliminar_imagen(paciente.imagen_2)
                paciente.imagen_2 = None

            # Guardar dentigrama canvas si se ha enviado
            data_url = request.form.get('dentigrama_canvas')
            if data_url and data_url.startswith("data:image"):
                try:
                    # Eliminar dentigrama anterior si existe y se está subiendo uno nuevo
                    if paciente.dentigrama_canvas:
                        eliminar_imagen(paciente.dentigrama_canvas)

                    filename_canvas = secure_filename(f"{uuid4().hex}_dentigrama_canvas.png")
                    ruta_guardado_abs_dentigrama = os.path.join(carpeta_destino_dentigrama_abs, filename_canvas)
                    header, encoded = data_url.split(",", 1)
                    with open(ruta_guardado_abs_dentigrama, "wb") as f:
                        f.write(base64.b64decode(encoded))
                    paciente.dentigrama_canvas = os.path.join('img', 'pacientes', 'dentigramas', filename_canvas).replace("\\", "/")
                except Exception as e_dent: # Excepción específica para el dentigrama

                    flash(f"Error al guardar el dentigrama: {str(e_dent)}", 'danger')
                    current_app.logger.error(f"Error al guardar dentigrama para paciente {id}: {e_dent}", exc_info=True)


            # Eliminar dentigrama anterior si se marcó el checkbox y no se subió uno nuevo
            if request.form.get('eliminar_dentigrama') and paciente.dentigrama_canvas and not (data_url and data_url.startswith("data:image")):
                eliminar_imagen(paciente.dentigrama_canvas)
                paciente.dentigrama_canvas = None

            # Registrar nueva evolución si se escribió algo
            nueva_evolucion_desc = request.form.get('nueva_evolucion') # Renombrado para evitar conflicto
            if nueva_evolucion_desc and nueva_evolucion_desc.strip():
                evolucion_obj = Evolucion(descripcion=nueva_evolucion_desc.strip(), paciente_id=paciente.id)
                db.session.add(evolucion_obj) # Renombrado para evitar conflicto con la variable evolucion del bucle (si hubiera)

            # --- FIN LÓGICA DE IMÁGENES Y DENTIGRAMA ---
            print(f"DEBUG: Guardando dentigrama como: {paciente.dentigrama_canvas}")
            
            db.session.commit() # Commit final si todo fue bien
            flash('Paciente actualizado correctamente', 'success')
            return redirect(url_for('pacientes.mostrar_paciente', id=paciente.id))

        except Exception as e:
            db.session.rollback()
            flash('Ocurrió un error al actualizar el paciente.', 'danger')
            current_app.logger.error(f'Error al editar paciente {id}: {e}', exc_info=True)

            return render_template('editar_paciente.html', paciente=paciente, form_data=request.form)

    # Usamos la variable 'paciente' que SÍ existe
    form_data_inicial = {key: getattr(paciente, key, '') for key in paciente.__table__.columns.keys()}
    
    # Usamos 'paciente' aquí también
    if paciente.fecha_nacimiento:
        form_data_inicial['fecha_nacimiento'] = paciente.fecha_nacimiento.strftime('%Y-%m-%d')

    # Y aquí
    return render_template('editar_paciente.html', paciente=paciente, form_data=form_data_inicial)