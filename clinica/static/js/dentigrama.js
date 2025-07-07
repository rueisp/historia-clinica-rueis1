// --- FRAGMENTO CORREGIDO Y MEJORADO ---

const canvas = document.getElementById('dentigrama_canvas');
const ctx = canvas.getContext('2d');
const dentigramaInput = document.getElementById('dentigrama_canvas_input'); // Referencia al input oculto

// Cargar imagen de fondo
const imagenFondo = new Image();

// --- INICIO DE LA MODIFICACIÓN ---
// 1. Leemos la URL del dentigrama desde el atributo 'data-dentigrama-url' del canvas
//    Este atributo lo habremos puesto en el HTML (ej. editar_paciente.html)
const dentigramaUrl = canvas.dataset.dentigramaUrl;

if (dentigramaUrl) {
    // 2. Si encontramos una URL, la usamos como fuente para la imagen de fondo
    console.log("Cargando dentigrama desde URL:", dentigramaUrl);
    imagenFondo.src = dentigramaUrl;
} else {
    // 3. Si no hay un atributo 'data-dentigrama-url', usamos una imagen por defecto
    //    Esto es útil para la página de 'registrar_paciente.html'
    console.warn("Atributo 'data-dentigrama-url' no encontrado. Usando dentigrama base.");
    imagenFondo.src = '/static/img/dentigrama1.png'; 
}
// --- FIN DE LA MODIFICACIÓN ---

let acciones = []; // Almacena las acciones de dibujo (puntos)
let dibujando = false;
let colorPincel = 'red'; // Renombrado para evitar conflicto con la variable 'color' si la usas globalmente
// Ajusta el canvas según el tamaño del contenedor y redibuja
function ajustarCanvas() {
    if (!imagenFondo.complete || imagenFondo.naturalWidth === 0) {
        // La imagen de fondo aún no está cargada o falló, no ajustar todavía
        console.warn("AjustarCanvas: Imagen de fondo no lista.");
        return;
    }
    const containerWidth = canvas.parentElement.clientWidth;
    // Calcula la proporción basada en la imagen de fondo cargada
    const proporcion = imagenFondo.naturalHeight / imagenFondo.naturalWidth;
    canvas.width = containerWidth;
    canvas.height = containerWidth * proporcion;

    // Redibuja TODO: fondo + acciones
    redibujarTodo();
}

imagenFondo.onload = function () {
    console.log("Imagen de fondo del dentigrama cargada.");
    ajustarCanvas(); // Ajusta y dibuja por primera vez cuando la imagen está lista
    // Opcional: Si quieres que el input oculto tenga la imagen base desde el inicio,
    // podrías llamar a prepararDentigramaParaEnvio() aquí, pero es mejor
    // hacerlo al enviar el formulario para asegurar la última versión.
    // prepararDentigramaParaEnvio();
};

imagenFondo.onerror = function() {
    console.error("Error al cargar la imagen de fondo del dentigrama: " + imagenFondo.src);
    // Podrías dibujar un mensaje de error en el canvas o mostrar una alerta al usuario
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "gray";
    ctx.fillRect(0,0, canvas.width, canvas.height);
    ctx.fillStyle = "white";
    ctx.textAlign = "center";
    ctx.fillText("Error al cargar dentigrama", canvas.width / 2, canvas.height / 2);
};

// Redibujar en cambios de tamaño de pantalla
window.addEventListener('resize', ajustarCanvas);

// --- Herramientas de Dibujo ---
canvas.addEventListener('mousedown', (e) => {
    dibujando = true;
    dibujar(e); // Para dibujar un punto al hacer click
});
canvas.addEventListener('mouseup', () => {
    if (dibujando) {
        dibujando = false;
        // Opcional: podrías llamar a prepararDentigramaParaEnvio() aquí si quieres
        // que cada trazo "guarde" en el input, pero puede ser mucho.
        // Mejor al enviar el formulario o con el botón dedicado.
    }
});
canvas.addEventListener('mousemove', dibujar);
// Para dispositivos táctiles (básico)
canvas.addEventListener('touchstart', (e) => {
    dibujando = true;
    dibujar(e.touches[0]); // Usar el primer toque
    e.preventDefault(); // Prevenir scroll
});
canvas.addEventListener('touchend', () => {
    if (dibujando) {
        dibujando = false;
    }
});
canvas.addEventListener('touchmove', (e) => {
    dibujar(e.touches[0]);
    e.preventDefault(); // Prevenir scroll
});


function cambiarColor(nuevoColor) {
    colorPincel = nuevoColor;
}

function dibujar(event) {
    if (!dibujando) return;
    const rect = canvas.getBoundingClientRect();
    // Ajuste para obtener coordenadas relativas al canvas correctas
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;

    ctx.fillStyle = colorPincel;
    ctx.beginPath();
    ctx.arc(x, y, 3 * scaleX, 0, Math.PI * 2); // Escalar también el radio del pincel
    ctx.fill();

    // Guardar coordenadas relativas para el redibujado responsivo
    acciones.push({ xRel: x / canvas.width, yRel: y / canvas.height, color: colorPincel, radioRel: (3 * scaleX) / canvas.width });
}

// Redibujar todo: fondo y acciones guardadas
function redibujarTodo() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Dibuja la imagen de fondo si está cargada
    if (imagenFondo.complete && imagenFondo.naturalWidth !== 0) {
        ctx.drawImage(imagenFondo, 0, 0, canvas.width, canvas.height);
    } else {
        // Opcional: dibujar un placeholder si la imagen de fondo aún no carga
        ctx.fillStyle = "#f0f0f0";
        ctx.fillRect(0,0,canvas.width, canvas.height);
        ctx.fillStyle = "#888";
        ctx.textAlign = "center";
        ctx.fillText("Cargando dentigrama...", canvas.width / 2, canvas.height / 2);
    }

    // Redibuja las acciones del usuario
    for (let a of acciones) {
        const x = a.xRel * canvas.width;
        const y = a.yRel * canvas.height;
        const radio = a.radioRel * canvas.width; // Radio escalado
        ctx.fillStyle = a.color;
        ctx.beginPath();
        ctx.arc(x, y, radio, 0, Math.PI * 2);
        ctx.fill();
    }
}

function limpiarCanvas() {
    acciones = []; // Limpia solo las acciones del usuario
    redibujarTodo(); // Redibuja (esto mantendrá el fondo y quitará los trazos)
    // Opcional: Actualizar input si se limpia
    // prepararDentigramaParaEnvio();
}

// ESTA ES LA FUNCIÓN CLAVE QUE SE LLAMARÁ ANTES DE ENVIAR EL FORMULARIO
// Y también la puede llamar tu botón "Guardar" del canvas si lo mantienes.
function prepararDentigramaParaEnvio() {
    if (canvas && dentigramaInput) {
        dentigramaInput.value = canvas.toDataURL('image/png');
        console.log("Dentigrama preparado en input oculto para envío.");
        return true; // Indica éxito
    }
    console.error("Error: Canvas o input oculto para dentigrama no encontrado.");
    return false; // Indica fallo
}

// Función para el botón "Guardar" del canvas (si lo mantienes)
function accionBotonGuardarCanvas() {
    if(prepararDentigramaParaEnvio()) {
        alert("Los cambios del dentigrama están listos para ser guardados con el paciente. \n¡No olvides presionar 'Guardar' al final del formulario!");
    } else {
        alert("Hubo un error al preparar el dentigrama.");
    }
}

function deshacer() {
    if (acciones.length > 0) {
        acciones.pop();
        redibujarTodo();
        // Opcional: Actualizar input si se deshace
        // prepararDentigramaParaEnvio();
    }
}

// Detectar Ctrl+Z (o Cmd+Z en Mac)
document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        deshacer();
    }
});

// --- INICIALIZACIÓN ---
// Asegurarse de que ajustarCanvas se llame si la imagen ya estaba en caché y 'load' no se dispara
if (imagenFondo.complete && imagenFondo.naturalWidth !== 0) {
    imagenFondo.onload(); // Llama manualmente al handler onload
}