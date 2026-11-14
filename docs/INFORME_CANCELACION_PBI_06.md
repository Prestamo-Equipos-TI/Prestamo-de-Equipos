# PBI-06 — Cancelación de solicitudes y préstamos

## Flujo implementado

| Estado previo | Quién cancela | Estado resultante | Equipo |
| --- | --- | --- | --- |
| Pendiente | Solicitante propietario o gestor TI | Cancelado | Sin cambio |
| Aprobado, sin entrega | Gestor TI | Cancelado | Se libera solo si no hay otra restricción |
| Entregado | Gestor TI | Cancelación pendiente de devolución | No se libera |
| Cancelación pendiente, con recepción física | Gestor TI | Cancelado | Se determina por condición, averías, otras reservas o préstamos y actividad del equipo |

El motivo de cancelación es obligatorio. Cada paso de cancelación registra actor, motivo, fecha y estados anterior y nuevo en `RegistroEstadoSolicitud`. El solicitante ve su propio historial; gestión TI puede consultar todos. Se envían alertas al afectado o a TI según quién actúe.

Las acciones de cambio de estado se realizan en una transacción y bloquean la solicitud y el equipo. Una segunda acción sobre una solicitud ya cancelada o devuelta se rechaza. Los préstamos con cancelación pendiente siguen en las listas de equipos prestados y devoluciones, así como en la detección de vencimientos y averías.

## Verificación

`prestamos.test_cancelacion` cubre permisos, motivo, auditoría, alertas, los tres estados iniciales, devolución física, restricciones de avería y reserva, acceso al historial y doble acción. Ejecutar con `DATABASE_URL=sqlite:///:memory:` y una `SECRET_KEY` de prueba.

## Despliegue

Aplicar la migración `prestamos.0007` antes de servir el código nuevo. La base PostgreSQL de producción puede tener migraciones anteriores pendientes; verificar y aplicar la cadena de migraciones de forma controlada antes de desplegar. Los archivos de `staticfiles` de CSS y JavaScript se sincronizaron con `static` porque el servicio desplegado usa esa carpeta.
