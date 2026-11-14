# PBI-09: alcance de los reportes

Los seis puntos de exportación originales aceptan PDF y Excel y reutilizan `config.reportes.exportar_reporte`. El acceso a todos requiere sesión y el rol administrador TI o superadministrador (`solo_gestor_ti`). PDF usa ReportLab y Excel usa openpyxl.

| Reporte | Vista | Fuente y período |
| --- | --- | --- |
| Inventario | `inventario.views.inventario_lista` | `Equipo` activo. Fotografía actual, sin período; filtros de búsqueda, estado, categoría, modelo, ubicación, nombre y marca. |
| Solicitudes de préstamo | `prestamos.views.solicitudes_admin` | `SolicitudPrestamo.fecha_solicitud` |
| Historial por usuario | `historial.views.historial_usuarios` | `SolicitudPrestamo.fecha_solicitud`; el resumen incluye usuarios con solicitudes del período. |
| Detalle de usuario | `historial.views.historial_usuario_detalle` | `SolicitudPrestamo.fecha_solicitud`, limitado al usuario de la URL. |
| Historial por equipo | `historial.views.historial_equipos` | Préstamos por `SolicitudPrestamo.fecha_solicitud` y averías por `ReporteAveria.fecha_reporte`; el resumen incluye equipos con movimientos del período. |
| Detalle de equipo | `historial.views.historial_equipo_detalle` | Mismos campos, limitados al equipo de la URL. |

Las fechas límite son inclusivas. Las vistas generan las mismas secciones de datos para ambos formatos. La fecha de generación utiliza `TIME_ZONE` de Django, actualmente `UTC`. El logotipo procede de `static/img/campbell_logo.png`; los controles conservan las clases visuales y la navegación HTMX existentes.

La exportación adicional de **Mis alertas** (`alertas.views.alertas_lista`) ofrece solo PDF. Filtra `Alerta.fecha_creacion` y `Alerta.tipo` y contiene únicamente las alertas del usuario autenticado. El PDF está reservado a administradores TI y superadministradores; los demás usuarios conservan su lista personal sin opción de exportación.
