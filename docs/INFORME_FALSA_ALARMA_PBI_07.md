# PBI-07 — Cierre de averías por falsa alarma

Gestión TI puede cerrar como falsa alarma un reporte pendiente o en revisión, con motivo obligatorio. El reporte original permanece; el cierre registra actor, fecha, estado anterior y nuevo, y motivo en `RegistroCierreAveria`. El historial es consultable desde la lista de reportes. Una segunda acción de cierre sobre el mismo reporte se rechaza.

El equipo solo pasa a `disponible` cuando no tiene préstamo físico activo, reserva aprobada, mantenimiento, otra avería activa ni está inactivo. Si alguna restricción existe, el estado refleja esa restricción. El reportador recibe una alerta cuando otra persona cierra el caso.

La migración `averias.0002` agrega el nuevo estado y la tabla de auditoría. Para la base PostgreSQL local, también se requiere aplicar las migraciones pendientes de `usuarios` y `prestamos` ya presentes en la rama.

Verificación: `averias.test_falsa_alarma` cubre permisos, motivo, auditoría, alertas, cierre doble, estado en revisión, cierre previo, historial y restricciones de equipo. La suite completa se ejecuta sobre una base de pruebas PostgreSQL aislada.
