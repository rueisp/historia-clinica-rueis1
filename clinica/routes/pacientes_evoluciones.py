# app/routes/pacientes_evoluciones.py
from flask import Blueprint, redirect, url_for, flash, request, render_template, current_app
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Paciente, Evolucion # Solo los modelos que necesitas aquí

# ¡Nuevo Blueprint! Nota el nuevo nombre 'evoluciones'
evoluciones_bp = Blueprint('evoluciones', __name__, url_prefix='/pacientes')


# En routes/pacientes_evoluciones.py

@evoluciones_bp.route('/editar_evolucion/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_evolucion(id):
    # 1. Obtener la evolución y cargar su paciente asociado para la verificación
    #    Usamos joinedload para que la consulta sea más eficiente.
    from sqlalchemy.orm import joinedload
    evolucion = Evolucion.query.options(joinedload(Evolucion.paciente)).get_or_404(id)

    # --- INICIO DE LA VERIFICACIÓN DE PERMISOS ---
    
    # 2. Comprobar si el usuario actual es el dueño del paciente de esta evolución.
    #    Los administradores tienen permiso para todo.
    if not current_user.is_admin and evolucion.paciente.odontologo_id != current_user.id:
        flash("Acceso denegado. No tienes permiso para editar esta evolución.", "danger")
        # Lo redirigimos a la lista de sus propios pacientes para evitar confusiones.
        return redirect(url_for('pacientes.lista_pacientes'))
        
    # --- FIN DE LA VERIFICACIÓN DE PERMISOS ---
    # A partir de aquí, sabemos que el usuario tiene permiso.

    if request.method == 'POST':
        # La lógica de actualización se mantiene igual
        descripcion_form = request.form.get('descripcion', '').strip()
        
        if descripcion_form:
            evolucion.descripcion = descripcion_form
            try:
                db.session.commit()
                flash('Evolución actualizada correctamente.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar la evolución: {e}', 'danger')
                current_app.logger.error(f"Error al editar evolucion ID {id}: {e}", exc_info=True)
        else:
            flash('La descripción no puede estar vacía.', 'warning')

        # Redirigir de vuelta al perfil del paciente
        return redirect(url_for('pacientes.mostrar_paciente', id=evolucion.paciente_id))

    # Si el método es GET, simplemente mostramos la plantilla de edición
    return render_template('editar_evolucion.html', evolucion=evolucion)


@evoluciones_bp.route('/agregar_evolucion/<int:paciente_id>', methods=['POST'])
def agregar_evolucion(paciente_id):
    descripcion = request.form['descripcion']
    nueva = Evolucion(descripcion=descripcion, paciente_id=paciente_id)
    db.session.add(nueva)
    db.session.commit()
    flash('Evolución guardada exitosamente.', 'success')
    return redirect(url_for('pacientes.mostrar_paciente', id=paciente_id))


# En routes/pacientes_evoluciones.py

@evoluciones_bp.route('/eliminar_evolucion/<int:id>', methods=['POST'])
@login_required # Asegúrate siempre de que las rutas de acción estén protegidas
def eliminar_evolucion(id):
    # 1. Obtener la evolución y su paciente asociado para la verificación
    from sqlalchemy.orm import joinedload
    evolucion = Evolucion.query.options(joinedload(Evolucion.paciente)).get_or_404(id)

    # --- INICIO DE LA VERIFICACIÓN DE PERMISOS ---
    
    # 2. Comprobar si el usuario actual es el dueño del paciente de esta evolución.
    #    Los administradores (is_admin) pueden saltarse esta comprobación.
    if not current_user.is_admin and evolucion.paciente.odontologo_id != current_user.id:
        flash("Acceso denegado. No tienes permiso para eliminar esta evolución.", "danger")
        # Redirigir a un lugar seguro, como la lista de sus propios pacientes.
        return redirect(url_for('pacientes.lista_pacientes'))
        
    # --- FIN DE LA VERIFICACIÓN DE PERMISOS ---
    # A partir de aquí, sabemos que el usuario tiene permiso para eliminar.

    paciente_id = evolucion.paciente_id # Guardamos el ID para la redirección

    try:
        # IMPORTANTE: Aquí estás haciendo un borrado físico (hard delete).
        # Esto es diferente del "soft delete" que usas para pacientes y citas.
        # Si quieres ser consistente, deberías añadir un campo 'is_deleted' a tu modelo Evolucion
        # y aquí harías:
        # evolucion.is_deleted = True
        # Pero si el borrado físico es intencional para las evoluciones, déjalo así.
        
        db.session.delete(evolucion)
        db.session.commit()
        flash("Evolución eliminada exitosamente.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar la evolución: {str(e)}", "danger")
        current_app.logger.error(f"Error al eliminar evolucion ID {id}: {e}", exc_info=True)

    # La lógica de redirección se mantiene, pero ya no necesitas el 'origen'
    # si siempre rediriges al perfil. Si lo usas, está bien dejarlo.
    return redirect(url_for('pacientes.mostrar_paciente', id=paciente_id))