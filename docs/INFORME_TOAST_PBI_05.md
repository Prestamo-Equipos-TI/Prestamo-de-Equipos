# PBI-05: ciclo de vida del toast

El 13/11/2026 se compararon los archivos públicos de `https://controlit.onrender.com/` con el repositorio. El servicio entrega una revisión anterior de `inventario.js` (sin las acciones de usuarios de PBI-01), aunque las funciones antiguas del toast y sus reglas CSS coincidían con las locales. Por eso la diferencia observada no identifica por sí sola una causa única en el servicio. La corrección queda preparada en los dos directorios que usa el proyecto: `static` para desarrollo y `staticfiles` para el servicio, con `?v=pbi05` en la plantilla para renovar la caché del navegador.

Los avisos de éxito, error y alerta comparten ahora un cierre a los 4,5 segundos. Cada uno tiene una X accesible que cancela su temporizador. Al finalizar la transición se eliminan el nodo, sus listeners y sus temporizadores; un temporizador de respaldo cubre navegadores sin evento de transición. El contenedor vacío se elimina para que no quede una capa sobre la página. Al recuperar una pestaña suspendida se cierran avisos vencidos; `pagehide` limpia avisos y sondeos, y las consultas simultáneas de alertas se deduplican.

Pruebas: `node --test scripts/test_toasts.cjs` cubre autocierre, cierre manual, varios avisos, pestaña suspendida, limpieza al salir, consultas simultáneas, navegación HTMX y recarga. La batería de Django también pasó. No hubo migraciones ni cambios de apariencia fuera de la X requerida. La ventana de Chrome disponible estaba minimizada y no se pudo capturar una revisión visual manual.

Para comprobar el servicio, desplegar el commit que contiene PBI-05, verificar que `/static/js/inventario.js?v=pbi05` entrega la función nueva y probar un aviso de éxito y una alerta en una sesión real. Este trabajo no despliega el servicio por sí mismo.
