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

function refrescarInventario() {
    if (window.htmx) {
        htmx.ajax('GET', '/inventario/', {
            target: '#app-main',
            swap: 'innerHTML'
        });
    }
}

document.body.addEventListener('htmx:afterRequest', function (event) {
    const elemento = event.detail.elt;
    const statusCode = event.detail.xhr.status;

    if (!elemento) {
        return;
    }

    const esFormularioEquipo = elemento.id === 'equipo-form';
    const esDesactivarEquipo = elemento.classList.contains('danger');
    const fueCorrecto = statusCode === 204;

    if ((esFormularioEquipo || esDesactivarEquipo) && fueCorrecto) {
        cerrarModal(true);

        setTimeout(function () {
            refrescarInventario();
        }, 240);
    }
});