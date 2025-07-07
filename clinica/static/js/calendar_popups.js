// static/js/calendar_popups.js
document.addEventListener("DOMContentLoaded", function() {
    const calendarContainer = document.querySelector(".calendar-container");

    // Si no hay contenedor de calendario en la página, no hacer nada.
    if (!calendarContainer) {
        // console.warn("Contenedor del calendario no encontrado. El script de popups no se activará.");
        return;
    }

    function closeAllPopups(exceptPopup = null) {
        calendarContainer.querySelectorAll(".appointments-popup").forEach(popup => {
            if (popup !== exceptPopup) {
                popup.style.display = "none";
                const dayId = popup.id.replace('popup-', '');
                const button = calendarContainer.querySelector(`.toggle-appointments-popup[data-day-id="${dayId}"]`);
                if (button) {
                    button.textContent = "Ver citas";
                }
            }
        });
    }

    // Usar delegación de eventos en el contenedor del calendario
    calendarContainer.addEventListener("click", function(event) {
        const toggleButton = event.target.closest(".toggle-appointments-popup");
        const closeButton = event.target.closest(".close-popup");

        if (toggleButton) {
            event.stopPropagation(); // Previene que el clic se propague al 'document' (para el cierre por clic fuera)
            const dayId = toggleButton.dataset.dayId;
            const popup = document.getElementById(`popup-${dayId}`); // Los popups tienen IDs únicos globales

            if (!popup) return; // Si por alguna razón el popup no existe

            const isVisible = popup.style.display === "block";

            closeAllPopups(isVisible ? null : popup);

            if (isVisible) {
                popup.style.display = "none";
                toggleButton.textContent = "Ver citas";
            } else {
                popup.style.display = "block";
                toggleButton.textContent = "Ocultar citas";

                // Lógica de posicionamiento del popup
                const rect = popup.getBoundingClientRect();
                // const calendarContainerRect = calendarContainer.getBoundingClientRect(); // Ya tenemos calendarContainer

                // Ajuste horizontal
                if (rect.right > (window.innerWidth || document.documentElement.clientWidth) - 10) {
                    popup.style.left = 'auto';
                    popup.style.right = '5px';
                } else if (rect.left < 10) {
                    popup.style.left = '5px';
                    popup.style.right = 'auto';
                } else {
                    popup.style.left = '0'; // Por defecto
                    popup.style.right = 'auto';
                }

                // Ajuste vertical
                const dayCell = toggleButton.closest('.day'); // El botón que fue clickeado
                // const dayCellRect = dayCell.getBoundingClientRect(); // No se usa directamente aquí pero es útil para debug

                if (rect.bottom > (window.innerHeight || document.documentElement.clientHeight) - 10) {
                    // Intenta posicionar arriba de la celda del día si no hay espacio abajo
                    popup.style.top = 'auto';
                    popup.style.bottom = (dayCell.offsetHeight + 5) + 'px'; // 5px de margen
                } else {
                    // Por defecto: abajo de la celda del día
                    popup.style.top = (dayCell.offsetHeight + 5) + 'px'; // 5px de margen
                    popup.style.bottom = 'auto';
                }
            }
        } else if (closeButton) {
            event.stopPropagation();
            const popup = closeButton.closest(".appointments-popup");
            if (popup) {
                popup.style.display = "none";
                const dayId = popup.id.replace('popup-', '');
                const associatedToggleButton = calendarContainer.querySelector(`.toggle-appointments-popup[data-day-id="${dayId}"]`);
                if (associatedToggleButton) {
                    associatedToggleButton.textContent = "Ver citas";
                }
            }
        }
    });

    // Clic fuera del popup o del botón de toggle para cerrar todos los popups
    document.addEventListener("click", function(event) {
        // Verifica si el clic fue en un botón de toggle o dentro de un popup abierto
        const isToggleButton = event.target.closest(".toggle-appointments-popup");
        const isInsidePopup = event.target.closest(".appointments-popup");

        // Solo cerrar si el clic es fuera Y el contenedor del calendario existe
        if (!isToggleButton && !isInsidePopup && calendarContainer) {
            closeAllPopups();
        }
    });
});