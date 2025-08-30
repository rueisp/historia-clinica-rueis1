// ===================================================================
// DENTIGRAMA.JS - VERSIÓN UNIFICADA Y CORREGIDA
// Asegúrate de que este sea el ÚNICO script de dentigrama cargado en tu HTML.
// ===================================================================

document.addEventListener('DOMContentLoaded', function() {

    const canvas = document.getElementById('dentigrama_canvas');

    if (!canvas) {
        console.warn("No se encontró el canvas 'dentigrama_canvas' en esta página.");
        return;
    }

    const ctx = canvas.getContext('2d');
    const dentigramaUrlInput = document.getElementById('dentigrama_url_input');

    // --- Variables de Estado Unificadas ---
    let modoActual = 'pincel'; // 'pincel', 'check'
    let colorPincel = 'red'; 
    let dibujando = false;
    let ultimoX = 0; 
    let ultimoY = 0;
    
    // Almacena las acciones para deshacer (historial)
    let acciones = [];

    // --- Carga de la Imagen de Fondo (Overlay) ---
    // Esta imagen es la que se carga si ya hay un dentigrama guardado.
    const imagenOverlaySrc = document.getElementById('dentigrama_overlay_src');
    if (imagenOverlaySrc && imagenOverlaySrc.src) {
        const img = new Image();
        img.crossOrigin = "Anonymous";
        img.src = imagenOverlaySrc.src;
        img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            // Guardar el estado inicial después de cargar la imagen
            guardarEstadoInicialEnHistorial(); 
            // Esto es necesario para que el deshacer funcione correctamente
        };
        img.onerror = () => {
            console.error("Error al cargar la imagen de overlay del dentigrama.");
            guardarEstadoInicialEnHistorial(); // Guardar estado incluso si falla la carga
        };
    } else {
        guardarEstadoInicialEnHistorial(); // Si no hay imagen previa, guarda el canvas vacío
    }

    function guardarEstadoInicialEnHistorial() {
        // Guarda el estado actual del canvas (con o sin imagen de fondo) como la primera acción
        acciones.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
    }


    // --- Funciones de Dibujo ---

    // Función para dibujar el check de forma vectorial (líneas)
    function dibujarCheckVectorial(x, y, size = 20, color = 'purple', lineWidth = 3) {
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        ctx.beginPath();
        ctx.moveTo(x - size * 0.4, y);
        ctx.lineTo(x - size * 0.1, y + size * 0.4);
        ctx.lineTo(x + size * 0.4, y - size * 0.4);
        ctx.stroke();
    }

    // Redibuja todo el contenido del canvas desde el historial de acciones
    function redibujarTodo() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Cargar la imagen de fondo (si la hay) antes de redibujar acciones
        if (imagenOverlaySrc && imagenOverlaySrc.src) {
            const img = new Image();
            img.crossOrigin = "Anonymous";
            img.src = imagenOverlaySrc.src;
            img.onload = () => {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                // Redibujar las acciones encima
                acciones.forEach((accion, index) => {
                    if (index === 0) return; // La primera acción es el estado inicial (fondo)
                    ejecutarAccion(accion);
                });
            };
        } else {
            // Si no hay imagen de fondo, solo redibujamos las acciones desde el segunda entrada del historial
             acciones.forEach((accion, index) => {
                if (index === 0) return; // La primera acción es el estado inicial (canvas vacío)
                ejecutarAccion(accion);
            });
        }
    }

    // Función auxiliar para ejecutar una acción del historial
    function ejecutarAccion(accion) {
        if (accion.tipo === 'linea') {
            ctx.strokeStyle = accion.color;
            ctx.lineWidth = accion.ancho;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.beginPath();
            ctx.moveTo(accion.x1, accion.y1);
            ctx.lineTo(accion.x2, accion.y2);
            ctx.stroke();
        } else if (accion.tipo === 'check') {
            dibujarCheckVectorial(accion.x, accion.y, accion.size, accion.color, accion.lineWidth);
        }
    }


    // --- Utilidades ---
    // Obtiene las coordenadas del mouse/touch relativas al canvas
    const getCoords = (e) => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        let clientX = e.clientX, clientY = e.clientY;
        if (e.touches && e.touches.length) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        }
        return { x: (clientX - rect.left) * scaleX, y: (clientY - rect.top) * scaleY };
    };

    // --- Event Listeners Unificados para Mouse y Touch ---

    // Maneja tanto el inicio del pincel como la colocación del check
    canvas.addEventListener('mousedown', (e) => {
        const { x, y } = getCoords(e);
        
        if (modoActual === 'pincel') {
            dibujando = true;
            ultimoX = x;
            ultimoY = y;
            // Configurar el contexto para el pincel
            ctx.strokeStyle = colorPincel;
            ctx.lineWidth = 6;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
        } else if (modoActual === 'check') {
            const checkColor = 'purple'; // Color del check
            const checkSize = 20;       // Tamaño del check
            const checkLineWidth = 3;   // Grosor de línea del check
            
            // Dibujar el check
            dibujarCheckVectorial(x, y, checkSize, checkColor, checkLineWidth);
            
            // Guardar la acción del check en el historial
            acciones.push({
                tipo: 'check',
                x: x,
                y: y,
                size: checkSize,
                color: checkColor,
                lineWidth: checkLineWidth
            });

            // Restablecer al modo pincel después de dibujar el check
            modoActual = 'pincel';
        }
    });
    
    // Maneja el movimiento del pincel
    canvas.addEventListener('mousemove', (e) => {
        if (!dibujando || modoActual !== 'pincel') return;

        const { x, y } = getCoords(e);

        ctx.beginPath();
        ctx.moveTo(ultimoX, ultimoY);
        ctx.lineTo(x, y);
        ctx.stroke();

        // Guardar el segmento en el historial
        acciones.push({
            tipo: 'linea',
            x1: ultimoX,
            y1: ultimoY,
            x2: x,
            y2: y,
            color: colorPincel,
            ancho: 6
        });

        ultimoX = x;
        ultimoY = y;
    });

    // Maneja el fin del dibujo del pincel