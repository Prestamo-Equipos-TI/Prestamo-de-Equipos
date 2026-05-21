function moverIndicadorMenu(link) {
    const menuLinks = document.querySelector('.menu-links');
    const indicator = document.querySelector('.menu-indicator');

    if (!menuLinks || !indicator || !link) {
        return;
    }

    const containerRect = menuLinks.getBoundingClientRect();
    const linkRect = link.getBoundingClientRect();

    const top = linkRect.top - containerRect.top;

    indicator.style.transform = `translateY(${top}px)`;
    indicator.style.height = `${linkRect.height}px`;
    indicator.style.opacity = '1';
}

function activarMenu(page) {
    document.querySelectorAll('.menu-links a').forEach(function (item) {
        item.classList.remove('active');
    });

    const menuLink = document.querySelector('.menu-links a[data-page="' + page + '"]');

    if (menuLink) {
        menuLink.classList.add('active');
        moverIndicadorMenu(menuLink);
    }
}

function animarEntradaContenido() {
    const appMain = document.getElementById('app-main');

    if (!appMain) {
        return;
    }

    appMain.classList.remove('app-content-enter');

    void appMain.offsetWidth;

    appMain.classList.add('app-content-enter');
}

document.addEventListener('DOMContentLoaded', function () {
    const activeLink = document.querySelector('.menu-links a.active');

    if (activeLink) {
        setTimeout(function () {
            moverIndicadorMenu(activeLink);
        }, 40);
    }
});

document.addEventListener('click', function (event) {
    const link = event.target.closest('[data-page]');

    if (!link) {
        return;
    }

    const page = link.getAttribute('data-page');

    activarMenu(page);
});

document.addEventListener('htmx:afterSwap', function (event) {
    const activeLink = document.querySelector('.menu-links a.active');

    if (activeLink) {
        moverIndicadorMenu(activeLink);
    }

    if (event.detail.target && event.detail.target.id === 'app-main') {
        animarEntradaContenido();
    }
});

window.addEventListener('resize', function () {
    const activeLink = document.querySelector('.menu-links a.active');

    if (activeLink) {
        moverIndicadorMenu(activeLink);
    }
});