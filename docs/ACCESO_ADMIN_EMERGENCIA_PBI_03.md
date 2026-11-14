# PBI-03: acceso técnico de emergencia

`/admin/` permanece habilitado. Solo admite cuentas **activas** con las dos banderas técnicas de Django: `is_staff=True` e `is_superuser=True`. El rol funcional de Control IT no concede acceso a Django Admin. El formulario de ingreso también rechaza una cuenta que tenga solamente `is_staff`.

La gestión diaria de solicitantes, administradores TI y superadministradores secundarios se hace desde el panel **Usuarios** de Control IT. La designación o transferencia del principal se hace con el comando auditado `asignar_superadmin_principal` descrito en [la matriz de permisos](MATRIZ_PERMISOS_PBI_02.md).

## Validación antes de un despliegue

1. Confirmar en la base del entorno que existe al menos una cuenta técnica activa con ambas banderas y una contraseña recuperable por el responsable. No inferirlo del nombre de usuario ni del rol funcional.
2. Aplicar el código sin eliminar `/admin/`. Este PBI no añade migraciones.
3. Probar el inicio de sesión en `/admin/` con esa cuenta y comprobar que un usuario funcional sin las banderas técnicas no puede entrar.

La SQLite local de revisión conserva `administradorit` como cuenta técnica activa y principal funcional. Su acceso a Django Admin se valida en local; esta comprobación no afirma nada sobre las cuentas de PostgreSQL ni ejecuta cambios allí.

## Recuperación si se pierde el acceso técnico

Desde una consola autorizada con acceso a la configuración y base de datos del entorno, usar los comandos oficiales de Django `changepassword` para una cuenta técnica existente o `createsuperuser` para crear una cuenta técnica de emergencia. Verificar después el acceso a `/admin/` y custodiar las credenciales. El comando de asignación del principal funcional es independiente y no concede las banderas técnicas.
