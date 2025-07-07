// index.js

document.addEventListener('DOMContentLoaded', () => {
    // Definimos la variable de estado al principio, accesible para todas las funciones dentro del DOMContentLoaded
    let pacienteSeleccionado = null; 

    // ==================================================================
    // SECCIÓN: BÚSQUEDA DE PACIENTES Y PANEL DERECHO
    // ==================================================================
    const inputBusqueda = document.getElementById('busquedaPaciente');
    const contenedorSugerencias = document.getElementById('sugerencias');
    
    // --- Referencias a los botones y su contenedor ---
    const panelControles = document.getElementById('panel-controles');
    const btnEditarPacienteEl = document.getElementById('btnEditarPaciente');
    const btnVerCitasHistorialEl = document.getElementById('btnVerCitas');

    // --- Lógica de la Búsqueda ---
    if (inputBusqueda && contenedorSugerencias) {
        inputBusqueda.addEventListener('input', async () => {
            const query = inputBusqueda.value.trim();
            if (query.length < 2) { // Buena práctica: buscar a partir de 2 caracteres
                contenedorSugerencias.innerHTML = '';
                contenedorSugerencias.classList.add('hidden');
                return;
            }
            try {
                // La URL aquí está bien: /pacientes/buscar_sugerencias_ajax
                const response = await fetch(`/pacientes/buscar_sugerencias_ajax?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                contenedorSugerencias.innerHTML = '';
                if (!data.length) {
                    contenedorSugerencias.classList.add('hidden');
                    return;
                }
                data.forEach(paciente => {
                    const item = document.createElement('div');
                    item.className = 'px-4 py-2 cursor-pointer hover:bg-gray-100 rounded-xl transition-colors';
                    item.textContent = paciente.nombre;
                    item.addEventListener('click', async () => {
                        inputBusqueda.value = paciente.nombre;
                        contenedorSugerencias.classList.add('hidden');
                        try {
                            // La URL aquí está bien: /pacientes/obtener_paciente_ajax/...
                            const infoResponse = await fetch(`/pacientes/obtener_paciente_ajax/${paciente.id}`);
                            const datosPaciente = await infoResponse.json();
                            
                            // Actualizamos la variable de estado
                            pacienteSeleccionado = datosPaciente; 

                            // Llamamos a la función para rellenar el panel
                            actualizarPanelDerechoConPaciente(datosPaciente);
                            
                        } catch (error) {
                            console.error('Error al obtener datos del paciente:', error);
                        }
                    });
                    contenedorSugerencias.appendChild(item);
                });
                contenedorSugerencias.classList.remove('hidden');
            } catch (error) {
                console.error('Error al buscar sugerencias:', error);
            }
        });

        document.addEventListener('click', (e) => {
            if (!contenedorSugerencias.contains(e.target) && e.target !== inputBusqueda) {
                contenedorSugerencias.classList.add('hidden');
            }
        });
    }


    if (btnEditarPacienteEl && panelControles) {
        btnEditarPacienteEl.addEventListener('click', () => {
            // Verificamos si la variable de estado tiene un paciente
            if (pacienteSeleccionado && pacienteSeleccionado.id) {
                const urlBase = panelControles.dataset.editUrlBase;
                const urlFinal = urlBase.replace('/0/', `/${pacienteSeleccionado.id}/`);
                console.log("Intentando redirigir a:", urlFinal); 
                window.location.href = urlFinal;
            } else {
                alert('Por favor, busca y selecciona un paciente primero.');
            }
        });
    }

    if (btnVerCitasHistorialEl && panelControles) {
        btnVerCitasHistorialEl.addEventListener('click', () => {
            if (pacienteSeleccionado && pacienteSeleccionado.id) {
                const urlBase = panelControles.dataset.citasUrlBase;
                const urlFinal = urlBase.replace('/0/', `/${pacienteSeleccionado.id}/`);
                window.location.href = urlFinal;
            } else {
                alert('Por favor, busca y selecciona un paciente primero.');
            }
        });
    }

    // Función para actualizar el panel derecho
    function actualizarPanelDerechoConPaciente(datos) {
        const setText = (id, value, defaultValue = 'No especificado') => {
            const el = document.getElementById(id);
            if (el) el.textContent = value || defaultValue;
        };

        setText('nombrePaciente', datos.nombre);
        setText('generoEdad', `${datos.genero || 'N/A'} • ${datos.edad === 'No especificada' ? 'N/A' : (datos.edad + ' años') || 'N/A años'}`);
        setText('fechaNacimiento', datos.fecha_nacimiento);
        setText('estadoPaciente', datos.estado); // 'estado' aquí es el del paciente, ej. estado_civil
        setText('documentoPaciente', datos.documento);
        setText('telefonoPaciente', datos.telefono);
        setText('direccionPaciente', datos.direccion);
        setText('emailPaciente', datos.email);
        setText('ocupacionPaciente', datos.ocupacion);
        setText('aseguradoraPaciente', datos.aseguradora);
        setText('alergiasPaciente', datos.alergias);
        setText('enfermedadPaciente', datos.enfermedad_actual);

        // Actualizar información de citas específicas del paciente en el panel derecho
        setText('ultimaCita', datos.ultima_cita_info);
        setText('proximaCitaPanelDerecho', datos.proxima_cita_paciente_info);
        setText('motivoFrecuente', datos.motivo_frecuente_info);

        // Actualizar sección de imágenes
        const seccionImagenes = document.getElementById('seccion-imagenes');
        if (seccionImagenes) {
            seccionImagenes.innerHTML = ''; // Limpiar
            let imagenesHtml = '<p class="text-sm text-gray-500 mb-2">Imágenes y Dentigrama:</p><div class="grid grid-cols-2 gap-2">';
            let hayImagenes = false;
            const addImage = (url, alt) => {
                if (url) {
                    imagenesHtml += `<div><img src="${url}" alt="${alt}" class="rounded max-w-full h-auto shadow"></div>`;
                    hayImagenes = true;
                }
            };
            addImage(datos.imagen_1_url, "Imagen 1");
            addImage(datos.imagen_2_url, "Imagen 2");
            addImage(datos.dentigrama_url, "Dentigrama");
            
            imagenesHtml += '</div>';

            if (!hayImagenes && !datos.dentigrama_url) { // Si no hay ninguna imagen ni dentigrama
                 imagenesHtml = '<p class="text-sm text-gray-500">No hay imágenes ni dentigrama disponibles.</p>';
            }
            seccionImagenes.innerHTML = imagenesHtml;
        }
    }

    // ==================================================================
    // SECCIÓN: CITAS DE HOY (PANEL CENTRAL) - MANEJO DE ESTADOS Y FILTROS
    // ==================================================================
    const listaCitasContainer = document.getElementById('lista-citas-hoy');

    if (listaCitasContainer) {
        listaCitasContainer.addEventListener('click', function(event) {
            const botonCambiarEstado = event.target.closest('.btn-cambiar-estado');
            if (botonCambiarEstado) {
                event.preventDefault();
                const tarjetaCita = botonCambiarEstado.closest('.appointment-card');
                const citaId = tarjetaCita.dataset.citaId;
                const nuevoEstado = botonCambiarEstado.dataset.nuevoEstado;
                const estadoActual = tarjetaCita.dataset.estado;

                if (estadoActual === nuevoEstado) return;
                
                fetch(`/calendario/cita/actualizar_estado/${citaId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' /*, 'X-CSRFToken': TU_CSRF_TOKEN */ },
                    body: JSON.stringify({ estado: nuevoEstado })
                })
                .then(response => {
                    if (!response.ok) return response.json().then(err => { throw new Error(err.message || `Error: ${response.status}`) });
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        tarjetaCita.dataset.estado = data.nuevo_estado;
                        const estadoSpan = tarjetaCita.querySelector('.cita-estado-badge'); // Usar una clase específica
                        if (estadoSpan) {
                            estadoSpan.textContent = data.nuevo_estado.charAt(0).toUpperCase() + data.nuevo_estado.slice(1);
                            estadoSpan.className = 'cita-estado-badge text-xs px-2 py-0.5 rounded-full mt-1 inline-block'; // Reset base
                            if (data.nuevo_estado === 'completada') estadoSpan.classList.add('bg-green-100', 'text-green-700');
                            else if (data.nuevo_estado === 'cancelada') estadoSpan.classList.add('bg-red-100', 'text-red-700');
                            else estadoSpan.classList.add('bg-yellow-100', 'text-yellow-700');
                        }

                        const accionesDiv = tarjetaCita.querySelector('.appointment-actions');
                        if (accionesDiv) {
                            const btnCompletar = accionesDiv.querySelector('.btn-cambiar-estado[data-nuevo-estado="completada"]');
                            const btnPendiente = accionesDiv.querySelector('.btn-cambiar-estado[data-nuevo-estado="pendiente"]');
                            const btnCancelar = accionesDiv.querySelector('.btn-cambiar-estado[data-nuevo-estado="cancelada"]');

                            if (btnCompletar) btnCompletar.style.display = (data.nuevo_estado === 'completada' || data.nuevo_estado === 'cancelada') ? 'none' : 'inline-block';
                            if (btnPendiente) btnPendiente.style.display = (data.nuevo_estado === 'pendiente' || data.nuevo_estado === 'cancelada') ? 'none' : 'inline-block';
                            if (btnCancelar) btnCancelar.style.display = (data.nuevo_estado === 'cancelada') ? 'none' : 'inline-block';
                        }
                        
                        actualizarContadoresPestañasCitasHoy();

                        const filtroActivo = document.querySelector('.tab-appointment-filter[data-active="true"]');
                        if (filtroActivo && filtroActivo.dataset.status !== 'todas' && filtroActivo.dataset.status !== data.nuevo_estado) {
                            tarjetaCita.style.display = 'none';
                            verificarMensajeNoCitas(filtroActivo.dataset.status);
                        }
                    } else { alert("Error al actualizar: " + data.message); }
                })
                .catch(error => {
                    console.error('Error en fetch:', error);
                    alert('Error de red al actualizar cita: ' + error.message);
                });
            }
        });
    }

    function actualizarContadoresPestañasCitasHoy() {
        const setTextContent = (id, count) => {
            const el = document.getElementById(id);
            if (el) el.textContent = count;
        };
        setTextContent('count-todas', document.querySelectorAll('.appointment-card[data-estado]').length);
        setTextContent('count-pendientes', document.querySelectorAll('.appointment-card[data-estado="pendiente"]').length);
        setTextContent('count-completadas', document.querySelectorAll('.appointment-card[data-estado="completada"]').length);
        setTextContent('count-canceladas', document.querySelectorAll('.appointment-card[data-estado="cancelada"]').length);
    }

    const tabsCitasHoy = document.querySelectorAll(".tab-appointment-filter");
    const noAppointmentsMessageCitasHoy = document.querySelector(".no-appointments-message");

    tabsCitasHoy.forEach(tab => {
        tab.addEventListener("click", () => {
            tabsCitasHoy.forEach(t => t.dataset.active = "false");
            tab.dataset.active = "true";
            const statusToShow = tab.dataset.status;
            filtrarTarjetasCita(statusToShow);
        });
    });
    
    function filtrarTarjetasCita(statusToShow) {
        const todasLasTarjetasCitas = document.querySelectorAll(".appointment-card"); // Obtener siempre la lista actual
        let visibleCount = 0;
        todasLasTarjetasCitas.forEach(card => {
            const cardStatus = card.dataset.estado;
            if (statusToShow === 'todas' || cardStatus === statusToShow) {
                card.style.display = ''; // O tu display por defecto para las tarjetas
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        verificarMensajeNoCitas(statusToShow, visibleCount, todasLasTarjetasCitas.length);
    }
    
    function verificarMensajeNoCitas(statusMostrando, conteoVisible, conteoTotal) {
        if (noAppointmentsMessageCitasHoy) {
            if (conteoVisible === 0) {
                noAppointmentsMessageCitasHoy.style.display = ''; // o 'block'
                const textoMensajeP = noAppointmentsMessageCitasHoy.querySelector('p');
                if (textoMensajeP) {
                    let texto = `No hay citas ${statusMostrando === 'todas' ? 'programadas' : statusMostrando} para hoy.`;
                    if (statusMostrando !== 'todas' && conteoTotal > 0) { // Si hay citas en total pero ninguna coincide con el filtro
                        texto = `No hay citas que coincidan con el filtro '${statusMostrando}'.`;
                    } else if (statusMostrando === 'todas' && conteoTotal === 0) { // No hay citas en absoluto
                        texto = 'No hay citas programadas para hoy.';
                    }
                    textoMensajeP.textContent = texto;
                }
            } else {
                noAppointmentsMessageCitasHoy.style.display = 'none';
            }
        }
    }

    // Llamada inicial
    const todasLasTarjetasIniciales = document.querySelectorAll(".appointment-card");
    if (listaCitasContainer && todasLasTarjetasIniciales.length > 0) { 
        actualizarContadoresPestañasCitasHoy();
        const tabTodas = document.querySelector('.tab-appointment-filter[data-status="todas"]');
        if (tabTodas) {
            tabTodas.dataset.active = "true"; // Asegurar que "todas" esté activo
            filtrarTarjetasCita("todas");
        }
    } else if (noAppointmentsMessageCitasHoy) {
        noAppointmentsMessageCitasHoy.style.display = '';
        const textoMensajeP = noAppointmentsMessageCitasHoy.querySelector('p');
        if (textoMensajeP) textoMensajeP.textContent = 'No hay citas programadas para hoy.';
        actualizarContadoresPestañasCitasHoy(); 
    }

    // ==================================================================
    // SECCIÓN: PESTAÑAS DEL PANEL DERECHO (TU FUNCIÓN mostrarSeccion)
    // ==================================================================
    function mostrarSeccion(seccionIdActiva) {
        // IDs de las secciones del panel derecho que se pueden mostrar/ocultar
        const idsSeccionesPanelDerecho = ['datos', 'citas', 'imagenes']; // Asegúrate que estos IDs correspondan a los 'seccion-id'
        
        idsSeccionesPanelDerecho.forEach(idPanel => {
            const el = document.getElementById(`seccion-${idPanel}`);
            if (el) el.classList.add('hidden');
        });

        const seccionActivaEl = document.getElementById(`seccion-${seccionIdActiva}`);
        if (seccionActivaEl) seccionActivaEl.classList.remove('hidden');

        // Actualizar estilo de los botones de pestañas del panel DERECHO
        // Asumo que los botones de pestañas del panel derecho tienen la clase '.tab-btn-panel-derecho'
        document.querySelectorAll('.tab-btn-panel-derecho').forEach(btn => {
            btn.classList.remove('border-black', 'text-black', 'font-semibold'); // Quitar estado activo
            btn.classList.add('text-gray-600', 'border-transparent');
        });
        
        // Activar el botón correspondiente a la sección activa
        // Esto asume que los botones tienen un data-seccion="datos", data-seccion="citas", etc.
        const btnActiva = document.querySelector(`.tab-btn-panel-derecho[data-seccion="${seccionIdActiva}"]`);
        if (btnActiva) {
            btnActiva.classList.add('border-black', 'text-black', 'font-semibold');
            btnActiva.classList.remove('text-gray-600', 'border-transparent');
        }
    }

    // Añadir event listeners a los botones de pestañas del panel derecho
    document.querySelectorAll('.tab-btn-panel-derecho').forEach(btn => {
        btn.addEventListener('click', function() {
            const seccion = this.dataset.seccion; // ej. data-seccion="datos"
            if (seccion) {
                mostrarSeccion(seccion);
            }
        });
    });
    
    // Llamada inicial para mostrar la sección de 'datos' en el panel derecho si no hay paciente seleccionado,
    // o si `mostrarSeccion('datos')` no se llamó antes de que los listeners se adjunten.
    if (!pacienteSeleccionado) { // Solo si no hay un paciente ya cargado (ej. al inicio)
       const primerTabPanelDerecho = document.querySelector('.tab-btn-panel-derecho[data-seccion="datos"]');
       if(primerTabPanelDerecho) mostrarSeccion('datos'); // Mostrar 'datos' por defecto
    }


}); // Cierre del DOMContentLoaded principal