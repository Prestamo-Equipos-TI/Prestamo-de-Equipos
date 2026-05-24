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

document.body.addEventListener('htmx:beforeSwap', function (event) {
    const statusCode = event.detail.xhr.status;

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

    const esFormularioEquipo = elemento.id === 'equipo-form';
    const esFormularioPrestamo = elemento.id === 'prestamo-form';
    const esFormularioAprobacion = elemento.id === 'aprobar-solicitud-form';
    const esFormularioEntrega = elemento.id === 'entrega-form';
    const esFormularioDevolucion = elemento.id === 'devolucion-form';
    const esFormularioAveria = elemento.id === 'averia-form';
    const esFormularioAveriaAdmin = elemento.id === 'averia-admin-form';
    const esFormularioGestionAveria = elemento.id === 'gestionar-averia-form';
    const esFormularioResolverAveria = elemento.id === 'resolver-averia-form';
    const esDesactivarEquipo = elemento.classList.contains('danger');


    const accion = elemento.dataset.action;
    const esRechazarSolicitud = accion === 'rechazar-solicitud';

    const esEnlaceAlertas = elemento.dataset.page === 'alertas';

    if (esEnlaceAlertas && statusCode === 200) {
        limpiarIndicadoresAlertas();
    }

    const fueCorrecto = statusCode === 204;

    if (
        (
            esFormularioEquipo ||
            esFormularioPrestamo ||
            esFormularioAprobacion ||
            esFormularioEntrega ||
            esFormularioDevolucion ||
            esFormularioAveria ||
            esDesactivarEquipo ||
            esFormularioAveriaAdmin ||
            esFormularioGestionAveria ||
            esFormularioResolverAveria ||
            esRechazarSolicitud
        ) &&
        fueCorrecto
    ) {
        cerrarModal(true);

        setTimeout(function () {
            refrescarVistaActual();
        }, 240);
    }
});