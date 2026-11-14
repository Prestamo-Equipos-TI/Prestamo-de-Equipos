const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'static', 'js', 'inventario.js'), 'utf8');

function setup(storage = new Map()) {
    let now = 0;
    let nextId = 1;
    const timers = new Map();
    const schedule = (callback, delay, interval = false) => {
        const id = nextId++;
        timers.set(id, { callback, at: now + delay, interval: interval ? delay : 0 });
        return id;
    };
    const cancel = id => timers.delete(id);
    const advance = milliseconds => {
        const end = now + milliseconds;
        while (true) {
            const due = [...timers.entries()].filter(([, timer]) => timer.at <= end)
                .sort((a, b) => a[1].at - b[1].at)[0];
            if (!due) break;
            const [id, timer] = due;
            now = timer.at;
            timers.delete(id);
            if (timer.interval) timers.set(id, { ...timer, at: now + timer.interval });
            timer.callback();
        }
        now = end;
    };

    class Element {
        constructor() {
            this.children = [];
            this.listeners = new Map();
            const classes = new Set();
            this.classList = {
                add: name => classes.add(name),
                remove: name => classes.delete(name),
                contains: name => classes.has(name),
            };
        }
        appendChild(child) { child.parentElement = this; this.children.push(child); return child; }
        remove() {
            if (!this.parentElement) return;
            this.parentElement.children = this.parentElement.children.filter(child => child !== this);
            this.parentElement = null;
        }
        setAttribute(name, value) { this[name] = value; }
        addEventListener(name, callback) {
            if (!this.listeners.has(name)) this.listeners.set(name, new Set());
            this.listeners.get(name).add(callback);
        }
        removeEventListener(name, callback) { this.listeners.get(name)?.delete(callback); }
        dispatch(name, extra = {}) {
            for (const callback of this.listeners.get(name) || []) callback({ target: this, ...extra });
        }
    }

    const body = new Element();
    const documentListeners = new Element();
    const windowListeners = new Element();
    const findId = (element, id) => element.id === id ? element :
        element.children.map(child => findId(child, id)).find(Boolean);
    const document = {
        body,
        hidden: false,
        createElement: () => new Element(),
        getElementById: id => findId(body, id),
        querySelector: () => null,
        addEventListener: (...args) => documentListeners.addEventListener(...args),
        dispatch: (...args) => documentListeners.dispatch(...args),
    };
    const window = {
        addEventListener: (...args) => windowListeners.addEventListener(...args),
        dispatch: (...args) => windowListeners.dispatch(...args),
    };
    const context = vm.createContext({
        document, window, console,
        Date: class extends Date { static now() { return now; } },
        setTimeout: (callback, delay) => schedule(callback, delay),
        clearTimeout: cancel,
        setInterval: (callback, delay) => schedule(callback, delay, true),
        clearInterval: cancel,
        requestAnimationFrame: callback => schedule(callback, 16),
        cancelAnimationFrame: cancel,
        sessionStorage: {
            getItem: key => storage.get(key) || null,
            setItem: (key, value) => storage.set(key, value),
        },
    });
    vm.runInContext(source, context);
    const run = expression => vm.runInContext(expression, context);
    const toasts = () => document.getElementById('toast-container')?.children || [];
    return { advance, body, context, document, run, timers, toasts, window,
        jump: milliseconds => { now += milliseconds; } };
}

test('el toast de éxito dura 4,5 segundos y libera el contenedor', () => {
    const ui = setup();
    ui.run("mostrarMensajeResultado('Guardado', 'exito')");
    ui.advance(4499);
    assert.equal(ui.toasts().length, 1);
    assert.equal(ui.toasts()[0].classList.contains('show'), true);
    ui.advance(1);
    assert.equal(ui.toasts()[0].classList.contains('hide'), true);
    ui.advance(350);
    assert.equal(ui.toasts().length, 0);
    assert.equal(ui.timers.size, 0);
});

test('la X cierra un error sin interferir con otra alerta', () => {
    const ui = setup();
    ui.run("mostrarMensajeResultado('Error', 'error')");
    ui.run("mostrarNuevaAlerta('Aviso', 'Mensaje')");
    assert.equal(ui.toasts().length, 2);
    assert.equal(ui.toasts()[0].children[2]['aria-label'], 'Cerrar aviso');
    ui.toasts()[0].children[2].dispatch('click');
    ui.advance(350);
    assert.equal(ui.toasts().length, 1);
    ui.advance(4500);
    assert.equal(ui.toasts().length, 0);
});

test('al volver de una pestaña suspendida se cierra el toast vencido', () => {
    const ui = setup();
    ui.run("mostrarNuevaAlerta('Aviso', 'Mensaje')");
    ui.jump(5000);
    ui.document.hidden = false;
    ui.document.dispatch('visibilitychange');
    assert.equal(ui.toasts()[0].classList.contains('hide'), true);
    ui.advance(350);
    assert.equal(ui.toasts().length, 0);
});

test('pagehide limpia toasts y sondeos', () => {
    const ui = setup();
    ui.document.dispatch('DOMContentLoaded');
    ui.run("mostrarMensajeResultado('Guardado')");
    assert.ok(ui.timers.size > 1);
    ui.window.dispatch('pagehide');
    assert.equal(ui.toasts().length, 0);
    assert.equal(ui.timers.size, 0);
});

test('dos consultas simultáneas no muestran la misma alerta dos veces', async () => {
    const ui = setup();
    let resolver;
    let llamadas = 0;
    ui.context.fetch = () => {
        llamadas++;
        return new Promise(resolve => { resolver = resolve; });
    };
    const primera = ui.run('consultarNuevasAlertas()');
    const segunda = ui.run('consultarNuevasAlertas()');
    assert.equal(llamadas, 1);
    resolver({ ok: true, json: async () => ({ hay_nueva: true, id: 7,
        titulo: 'Aviso', mensaje: 'Texto' }) });
    await Promise.all([primera, segunda]);
    assert.equal(ui.toasts().length, 1);
});

test('la navegación HTMX y la recarga no duplican alertas', async () => {
    const storage = new Map();
    const ui = setup(storage);
    ui.context.fetch = async () => ({ ok: true, json: async () => ({ hay_nueva: true,
        id: 11, titulo: 'Aviso', mensaje: 'Texto' }) });
    await ui.run('consultarNuevasAlertas()');
    assert.equal(ui.toasts().length, 1);
    ui.body.dispatch('htmx:afterRequest', { detail: { elt: { dataset: { page: 'dashboard' },
        classList: { contains: () => false } }, xhr: { status: 200 } } });
    await ui.run('consultarNuevasAlertas()');
    assert.equal(ui.toasts().length, 1);
    ui.window.dispatch('pagehide');

    const recargada = setup(storage);
    recargada.context.fetch = ui.context.fetch;
    await recargada.run('consultarNuevasAlertas()');
    assert.equal(recargada.toasts().length, 0);
});
