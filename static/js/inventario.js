function abrirModal() {
    document.body.classList.add('modal-open');
}

function cerrarModal() {
    document.body.classList.remove('modal-open');

    const modalContainer = document.getElementById('modal-container');

    if (modalContainer) {
        modalContainer.innerHTML = '';
    }
}

function volverInventario(url) {
    document.body.classList.remove('modal-open');
    window.location.href = url;
}