// Archivo: clinica/static/js/dentigrama_logic.js
document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('dentigrama_canvas');
    if (!canvas) return;

    canvas.width = 800;
    canvas.height = 400;

    const ctx = canvas.getContext('2d');
    const dentigramaUrlInput = document.getElementById('dentigrama_url_input');

    // --- Estado ---
    let historial = [];
    let dibujando = false;
    let primerPunto = false;
    let colorActual = 'black';
    let modoActual = 'pincel';

    // --- Precarga ---
    const imagenPrevia = document.getElementById('dentigrama_overlay_src');
    const guardarEstadoActual = () => {
        historial.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
        if (historial.length > 20) historial.shift();
    };

    if (imagenPrevia && imagenPrevia.src) {
        const img = new Image();
        img.crossOrigin = 'Anonymous';
        img.src = imagenPrevia.src;
        img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            historial = [ctx.getImageData(0, 0, canvas.width, canvas.height)];
        };
        img.onerror = () => {
            console.error('Error precargando dentigrama.');
            historial = [ctx.getImageData(0, 0, canvas.width, canvas.height)];
        };
    } else {
        historial = [ctx.getImageData(0, 0, canvas.width, canvas.height)];
    }

    // --- Utilidades ---
    const redibujarCanvas = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const ultimo = historial[historial.length - 1];
        if (ultimo) ctx.putImageData(ultimo, 0, 0);
    };

    const getCoords = (e) => {
        const rect = canvas.getBoundingClientRect();
        let clientX = e.clientX, clientY = e.clientY;
        if (e.touches && e.touches.length) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        }
        return { x: clientX - rect.left, y: clientY - rect.top };
    };

    // --- Dibujo ---
    const empezarDibujo = (e) => {
        dibujando = true;
        primerPunto = true;
        
        const { x, y } = getCoords(e);
        ctx.beginPath();
        ctx.strokeStyle = colorActual;
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        
        ctx.moveTo(x, y); 
    };

    const dibujar = (e) => {
        if (!dibujando) return;
        const { x, y } = getCoords(e);
        
        if (primerPunto) {
            primerPunto = false;
            return;
        }

        ctx.lineTo(x, y);
        ctx.stroke();
    };

    const finalizarDibujo = () => {
        if (!dibujando) return;
        dibujando = false;
        try { ctx.closePath(); } catch (_) { }
        guardarEstadoActual();
    };

    // --- Eventos de Puntero (mouse y touch) ---
    // 🚨 CAMBIO CLAVE: Unimos la lógica del pincel y del check en el mismo evento
    canvas.addEventListener('mousedown', (e) => {
        if (modoActual === 'pincel') {
            e.preventDefault();
            empezarDibujo(e);
        } else if (modoActual === 'check') {
            const { x, y } = getCoords(e);
            ctx.font = 'bold 30px Arial';
            ctx.fillStyle = 'purple';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('✔️', x, y);
            guardarEstadoActual();
            
            modoActual = 'pincel';
            colorActual = 'black';
            canvas.style.cursor = 'default';
            actualizarEstadoBotones();
        }
    });

    canvas.addEventListener('mousemove', (e) => {
        if (modoActual === 'pincel') dibujar(e);
    });

    canvas.addEventListener('mouseup', () => {
        if (modoActual === 'pincel') {
            finalizarDibujo();
        }
    });

    canvas.addEventListener('mouseout', () => {
        if (modoActual === 'pincel') finalizarDibujo();
    });

    // Eliminamos el evento 'click' para evitar la superposición
    // La lógica se ha movido al evento 'mousedown'
    // canvas.addEventListener('click', ...);

    // --- Touch (evita que además dispare eventos mouse/click) ---
    canvas.addEventListener('touchstart', (e) => {
        if (modoActual === 'pincel') {
            e.preventDefault();
            empezarDibujo(e);
        }
    }, { passive: false });

    canvas.addEventListener('touchmove', (e) => {
        if (modoActual === 'pincel') {
            e.preventDefault();
            dibujar(e);
        }
    }, { passive: false });

    canvas.addEventListener('touchend', (e) => {
        if (modoActual === 'pincel') {
            e.preventDefault();
            finalizarDibujo();
        }
    }, { passive: false });

    // --- Botonera ---
    const cambiarColor = (nuevoColor) => {
        colorActual = nuevoColor;
        modoActual = 'pincel';
        canvas.style.cursor = 'default';
        actualizarEstadoBotones();
    };

    const activarHerramientaCheck = () => {
        colorActual = 'blue';
        modoActual = 'check';
        canvas.style.cursor = 'crosshair';
        actualizarEstadoBotones();
    };

    const limpiarCanvas = () => {
        historial = [historial[0]];
        redibujarCanvas();
        guardarEstadoActual();
    };

    const deshacer = () => {
        if (historial.length > 1) {
            historial.pop();
            redibujarCanvas();
        } else if (historial.length === 1) {
            historial = [historial[0]];
            redibujarCanvas();
        }
    };

    const accionBotonGuardarCanvas = () => {
        const ultimo = historial[historial.length - 1];
        if (!ultimo) return alert('No hay nada para guardar.');
        canvas.toBlob(function (blob) {
            const formData = new FormData();
            formData.append('dentigrama_overlay', blob, 'dentigrama.png');
            fetch('/pacientes/upload_dentigrama', { method: 'POST', body: formData })
                .then(r => r.json())
                .then(d => {
                    if (d.url && dentigramaUrlInput) {
                        dentigramaUrlInput.value = d.url;
                        alert('¡Dentigrama actualizado!\nNo olvides guardar el formulario.');
                    } else {
                        alert('Error al subir el dentigrama: ' + (d.error || 'Respuesta desconocida'));
                    }
                })
                .catch(err => {
                    console.error('Error de red al subir a Cloudinary:', err);
                    alert('Hubo un error de conexión al subir el dentigrama.');
                });
        }, 'image/png');
    };

    function actualizarEstadoBotones() {
        document.querySelectorAll('.color-button').forEach(btn => {
            btn.classList.remove('active');
            if (modoActual === 'pincel' && btn.id === `btnColor${colorActual.charAt(0).toUpperCase() + colorActual.slice(1)}`) {
                btn.classList.add('active');
            }
        });
        document.getElementById('btnActivarCheck')?.classList.toggle('active', modoActual === 'check');
    }

    // Asignación de botones
    document.getElementById('btnColorRojo')?.addEventListener('click', () => cambiarColor('red'));
    document.getElementById('btnColorAzul')?.addEventListener('click', () => cambiarColor('blue'));
    document.getElementById('btnColorNegro')?.addEventListener('click', () => cambiarColor('black'));
    document.getElementById('btnActivarCheck')?.addEventListener('click', activarHerramientaCheck);
    document.getElementById('btnLimpiar')?.addEventListener('click', limpiarCanvas);
    document.getElementById('btnDeshacer')?.addEventListener('click', deshacer);
    document.getElementById('btnGuardarDentigrama')?.addEventListener('click', accionBotonGuardarCanvas);

    // Inicializar el estado de los botones y el contexto
    actualizarEstadoBotones();
});