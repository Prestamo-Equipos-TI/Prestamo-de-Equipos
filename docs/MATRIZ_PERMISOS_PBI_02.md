# PBI-02: roles funcionales y cuenta principal

| Operación | Solicitante | Administrador TI | Superadministrador secundario | Superadministrador principal |
| --- | --- | --- | --- | --- |
| Solicitar préstamo y consultar solicitudes propias | Sí | No desde el menú | No desde el menú | No desde el menú |
| Inventario, préstamos, averías e historial administrativos | No | Sí | Sí | Sí |
| Crear y gestionar solicitantes | No | Sí | Sí | Sí |
| Crear y gestionar administradores TI | No | No | Sí | Sí |
| Crear y gestionar superadministradores secundarios | No | No | No | Sí |
| Asignar o transferir la cuenta principal | No | No | No desde la web | Comando técnico auditado |
| Django Admin (`/admin/`) | Solo con `is_staff` e `is_superuser` técnicos | Solo con ambas banderas técnicas | Solo con ambas banderas técnicas | Solo con ambas banderas técnicas |

Las autorizaciones de la aplicación usan `PerfilUsuario.rol`, no `is_staff` ni `is_superuser`. El panel de usuarios no permite gestionar cuentas técnicas (`is_staff` o `is_superuser`), aunque una cuenta técnica designada principal sí puede actuar como gestora funcional. Crear un rol funcional nunca altera las banderas técnicas.

El principal se identifica con `PerfilUsuario.es_principal`, vinculado al ID de usuario. Una restricción única impide dos principales y otra exige que el principal tenga rol `superadmin`. Las vistas y señales impiden desactivarlo, degradarlo o eliminarlo. La migración deja todas las cuentas existentes sin principal para exigir una designación expresa.

## Designación inicial y recuperación

El comando requiere un operador técnico activo, el ID de la cuenta elegida repetido como confirmación y un motivo. Se ejecuta en la base de datos seleccionada por la configuración de Django:

```powershell
python manage.py asignar_superadmin_principal --usuario-id 1 --confirmar-id 1 --operador-id 1 --motivo "Designación aprobada"
```

Si la cuenta todavía no tiene perfil funcional, añadir `--carnet` y `--nombre-completo`. Para recuperar el control o transferir la titularidad a otra cuenta, repetir el comando con el ID nuevo y `--reemplazar`. La cuenta anterior conserva el rol de superadministrador secundario. Cada transferencia y cambio de rol queda en `RegistroGestionUsuario` con actor, fecha y motivo. El comando no cambia `is_staff` ni `is_superuser`.

En la SQLite local de revisión, el usuario confirmó expresamente `administradorit` como principal. Esto no implica aplicar la misma designación a PostgreSQL; para otro entorno hay que comprobar los IDs y autorizar su operación por separado.
