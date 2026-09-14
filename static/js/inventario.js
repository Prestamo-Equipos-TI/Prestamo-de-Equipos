function abrirModal() {
    document.body.classList.add('modal-open');
}


function cerrarModal(animado = false) {
    const modalContainer = document.getElementById('modal-container');

    if (!modalContainer) {
        return;
    }

    if (animado) {
        const backdrop = modalContainer.querySelector('.modal-backdrop-custom');

        if (backdrop) {
            backdrop.classList.add('modal-fade-out');
        }

        setTimeout(function () {
            document.body.classList.remove('modal-open');
            modalContainer.innerHTML = '';
        }, 220);

        return;
    }

    document.body.classList.remove('modal-open');
    modalContainer.innerHTML = '';
}


function volverInventario(url) {
    cerrarModal(true);

    setTimeout(function () {
        window.location.href = url;
    }, 220);
}


function refrescarVistaActual() {
    if (window.htmx) {
        htmx.ajax('GET', window.location.pathname, {
            target: '#app-main',
            swap: 'innerHTML'
        });
    }
}


function limpiarIndicadoresAlertas() {
    const indicadores = document.querySelectorAll(
        '.notification-dot, .sidebar-notification-dot'
    );

    indicadores.forEach(function (indicador) {
        indicador.remove();
    });
}


// =========================================================
// MENSAJES DE RESULTADO
// =========================================================

function mostrarMensajeResultado(mensaje, tipo = 'exito') {

    let contenedor = document.getElementById('toast-container');

    // Si todavía no existe, se crea automáticamente
    if (!contenedor) {
        contenedor = document.createElement('div');
        contenedor.id = 'toast-container';
        contenedor.className = 'toast-container';

        document.body.appendChild(contenedor);
    }

    const toast = document.createElement('div');

    toast.className = `result-toast ${tipo}`;

    const icono = tipo === 'exito' ? '✓' : '✕';

    toast.innerHTML = `
        <span class="result-toast-icon">
            ${icono}
        </span>

        <span class="result-toast-message">
            ${mensaje}
        </span>
    `;

    contenedor.appendChild(toast);

    // Permite que se ejecute la animación de entrada
    requestAnimationFrame(function () {
        toast.classList.add('show');
    });

    // Empieza a desaparecer después de 3 segundos
    setTimeout(function () {

        toast.classList.remove('show');

        toast.classList.add('hide');

        setTimeout(function () {
            toast.remove();
        }, 300);

    }, 3000);
}
// =========================================================
// TOAST DE NUEVAS ALERTAS
// =========================================================

function mostrarNuevaAlerta(titulo, mensaje) {

    let contenedor =
        document.getElementById('toast-container');

    if (!contenedor) {

        contenedor =
            document.createElement('div');

        contenedor.id =
            'toast-container';

        contenedor.className =
            'toast-container';

        document.body.appendChild(
            contenedor
        );
    }


    const toast =
        document.createElement('div');

    toast.className =
        'result-toast alerta';


    const icono =
        document.createElement('span');

    icono.className =
        'result-toast-icon';

    icono.textContent =
        '🔔';


    const contenido =
        document.createElement('div');

    contenido.className =
        'result-toast-content';


    const tituloElemento =
        document.createElement('strong');

    tituloElemento.className =
        'result-toast-title';

    tituloElemento.textContent =
        titulo;


    const mensajeElemento =
        document.createElement('span');

    mensajeElemento.className =
        'result-toast-message';

    mensajeElemento.textContent =
        mensaje;


    contenido.appendChild(
        tituloElemento
    );

    contenido.appendChild(
        mensajeElemento
    );


    toast.appendChild(
        icono
    );

    toast.appendChild(
        contenido
    );


    contenedor.appendChild(
        toast
    );


    requestAnimationFrame(
        function () {

            toast.classList.add(
                'show'
            );
        }
    );


    setTimeout(
        function () {

            toast.classList.remove(
                'show'
            );

            toast.classList.add(
                'hide'
            );


            setTimeout(
                function () {

                    toast.remove();

                },
                300
            );

        },
        5000
    );
}

// =========================================================
// INDICADOR DE ALERTAS DEL SIDEBAR
// =========================================================

function mostrarIndicadorAlertas() {

    const enlaceAlertas =
        document.querySelector(
            '[data-page="alertas"]'
        );

    if (!enlaceAlertas) {
        return;
    }


    const indicadorExistente =
        enlaceAlertas.querySelector(
            '.sidebar-notification-dot'
        );


    if (indicadorExistente) {
        return;
    }


    const indicador =
        document.createElement('span');

    indicador.className =
        'sidebar-notification-dot';


    enlaceAlertas.appendChild(
        indicador
    );
}
// =========================================================
// CONSULTAR NUEVAS ALERTAS
// =========================================================

async function consultarNuevasAlertas() {

    try {

        const respuesta =
            await fetch(
                '/alertas/nueva/',
                {
                    method: 'GET',

                    headers: {
                        'X-Requested-With':
                            'XMLHttpRequest'
                    },

                    credentials:
                        'same-origin'
                }
            );


        if (!respuesta.ok) {
            return;
        }


        const datos =
            await respuesta.json();


        if (!datos.hay_nueva) {
            return;
        }


        mostrarIndicadorAlertas();


        const ultimoIdGuardado =
            sessionStorage.getItem(
                'ultimaAlertaToast'
            );


        const idActual =
            String(datos.id);


        if (
            ultimoIdGuardado ===
            idActual
        ) {
            return;
        }


        mostrarNuevaAlerta(
            datos.titulo,
            datos.mensaje
        );


        sessionStorage.setItem(
            'ultimaAlertaToast',
            idActual
        );


    } catch (error) {

        console.error(
            'Error al consultar alertas:',
            error
        );
    }
}
// =========================================================
// MANEJO DE RESPUESTAS HTMX
// =========================================================

document.body.addEventListener('htmx:beforeSwap', function (event) {
    const statusCode = event.detail.xhr.status;

    // 422 se utiliza para devolver errores de validación
    // dentro de los formularios.
    if (statusCode === 422) {
        event.detail.shouldSwap = true;
        event.detail.isError = false;
    }
});


document.body.addEventListener('htmx:afterRequest', function (event) {

    const elemento = event.detail.elt;
    const statusCode = event.detail.xhr.status;

    if (!elemento) {
        return;
    }


    // =====================================================
    // IDENTIFICACIÓN DE OPERACIONES
    // =====================================================

    const esFormularioEquipo =
        elemento.id === 'equipo-form';

    const esFormularioPrestamo =
        elemento.id === 'prestamo-form';

    const esFormularioAprobacion =
        elemento.id === 'aprobar-solicitud-form';

    const esFormularioEntrega =
        elemento.id === 'entrega-form';

    const esFormularioDevolucion =
        elemento.id === 'devolucion-form';

    const esFormularioAveria =
        elemento.id === 'averia-form';

    const esFormularioAveriaAdmin =
        elemento.id === 'averia-admin-form';

    const esFormularioGestionAveria =
        elemento.id === 'gestionar-averia-form';

    const esFormularioResolverAveria =
        elemento.id === 'resolver-averia-form';


    const accion = elemento.dataset.action;

    const esRechazarSolicitud =
        accion === 'rechazar-solicitud';


    const esDesactivarEquipo =
        elemento.classList.contains('danger') &&
        !esRechazarSolicitud;


    // =====================================================
    // ALERTAS DEL SIDEBAR
    // =====================================================

    const esEnlaceAlertas =
        elemento.dataset.page === 'alertas';

    if (esEnlaceAlertas && statusCode === 200) {
        limpiarIndicadoresAlertas();
    }


    // =====================================================
    // ERRORES
    // =====================================================

    if (statusCode >= 400 && statusCode !== 422) {

        mostrarMensajeResultado(
            'No se pudo completar la operación.',
            'error'
        );

        return;
    }


    // =====================================================
    // OPERACIÓN EXITOSA
    // =====================================================

    const fueCorrecto = statusCode === 204;

    if (!fueCorrecto) {
        return;
    }


    // =====================================================
    // MENSAJE SEGÚN LA OPERACIÓN
    // =====================================================

    let mensajeResultado = 'Operación realizada correctamente.';


    if (esFormularioEquipo) {

        mensajeResultado =
            'Equipo guardado correctamente.';

    } else if (esFormularioPrestamo) {

        mensajeResultado =
            'Solicitud de préstamo enviada correctamente.';

    } else if (esFormularioAprobacion) {

        mensajeResultado =
            'Solicitud aprobada correctamente.';

    } else if (esRechazarSolicitud) {

        mensajeResultado =
            'Solicitud rechazada correctamente.';

    } else if (esFormularioEntrega) {

        mensajeResultado =
            'Entrega registrada correctamente.';

    } else if (esFormularioDevolucion) {

        mensajeResultado =
            'Devolución registrada correctamente.';

    } else if (esFormularioAveria) {

        mensajeResultado =
            'Reporte de avería enviado correctamente.';

    } else if (esFormularioAveriaAdmin) {

        mensajeResultado =
            'Reporte de avería registrado correctamente.';

    } else if (esFormularioGestionAveria) {

        mensajeResultado =
            'Avería actualizada correctamente.';

    } else if (esFormularioResolverAveria) {

        mensajeResultado =
            'Avería marcada como resuelta correctamente.';

    } else if (esDesactivarEquipo) {

        mensajeResultado =
            'Equipo eliminado correctamente.';
    }


    // =====================================================
    // MOSTRAR MENSAJE
    // =====================================================

    if (
        esFormularioEquipo ||
        esFormularioPrestamo ||
        esFormularioAprobacion ||
        esFormularioEntrega ||
        esFormularioDevolucion ||
        esFormularioAveria ||
        esFormularioAveriaAdmin ||
        esFormularioGestionAveria ||
        esFormularioResolverAveria ||
        esRechazarSolicitud ||
        esDesactivarEquipo
    ) {

        mostrarMensajeResultado(
            mensajeResultado,
            'exito'
        );

        cerrarModal(true);

        setTimeout(function () {
            refrescarVistaActual();
        }, 240);
    }
});


// =========================================================
// ERROR DE CONEXIÓN HTMX
// =========================================================

document.body.addEventListener('htmx:sendError', function () {

    mostrarMensajeResultado(
        'No se pudo conectar con el servidor.',
        'error'
    );
});


// =========================================================
// BÚSQUEDA AVANZADA DEL INVENTARIO
// =========================================================

function toggleBusquedaAvanzada() {

    const filtros =
        document.getElementById('advanced-filters');

    const boton =
        document.getElementById('advanced-search-toggle');

    if (!filtros || !boton) {
        return;
    }

    const estaAbierto =
        filtros.classList.contains('show');

    if (estaAbierto) {

        filtros.classList.remove('show');

        boton.innerHTML =
            '⚙ Búsqueda avanzada';

        boton.setAttribute(
            'aria-expanded',
            'false'
        );

    } else {

        filtros.classList.add('show');

        boton.innerHTML =
            '▲ Ocultar filtros';

        boton.setAttribute(
            'aria-expanded',
            'true'
        );
    }
}

// =========================================================
// MONITOREO DE NUEVAS ALERTAS
// =========================================================

document.addEventListener(
    'DOMContentLoaded',
    function () {

        // Primera comprobación unos segundos después
        // de cargar el sistema.
        setTimeout(
            consultarNuevasAlertas,
            3000
        );


        // Después comprueba cada 30 segundos.
        setInterval(
            consultarNuevasAlertas,
            30000
        );

    }
);