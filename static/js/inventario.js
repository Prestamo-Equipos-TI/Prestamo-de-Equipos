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
    const esDesactivarEquipo = elemento.classList.contains('danger');
    const fueCorrecto = statusCode === 204;

    if ((esFormularioEquipo || esFormularioPrestamo || esDesactivarEquipo) && fueCorrecto) {
        cerrarModal(true);

        setTimeout(function () {
            refrescarVistaActual();
        }, 240);
    }
});