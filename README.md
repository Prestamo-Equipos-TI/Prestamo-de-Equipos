
📖 Descripción del Proyecto

  Software de gestión diseñado para el Colegio Alexander Campbell. Su propósito principal es centralizar el control de los 
equipos tecnológicos (laptops, tablets, proyectores) que el colegio asigna a empleados y alumnos, permitiendo un seguimiento en tiempo real
y asegurando la integridad del inventario institucional.Con esta plataforma, se busca eliminar la dependencia de registros manuales, garantizando trazabilidad,
disponibilidad y un control riguroso de los activos.

✨ Características Principales

Gestión de Inventario: Registro detallado del estado de cada equipo (disponible, prestado, en mantenimiento) y actualización automática tras cada movimiento.
Control de Préstamos: Plataforma web que permite solicitar equipos en línea, con verificación de disponibilidad en tiempo real y flujo de aprobación digital.
Sistema de Alertas: Envío automático de notificaciones al aprobar o rechazar solicitudes, así como alertas de vencimientos próximos para devoluciones.
Reportes y Estadísticas: Generación de reportes sobre los equipos más solicitados y los tiempos promedio de préstamo para optimizar futuras adquisiciones.
Gestión de Usuarios: Perfiles diferenciados para alumnos, docentes, personal administrativo y técnicos de IT.

🛠️ Arquitectura y Tecnologías

El sistema se implementará bajo una arquitectura MVC (Modelo–Vista–Controlador) y cliente-servidor con acceso web.
Backend: Python utilizando el framework Django.
Frontend: JavaScript (React o Angular) para interfaces dinámicas, con diseño responsivo apoyado en Bootstrap o TailwindCSS.
Base de Datos: PostgreSQL con extensión PostGIS (o MySQL como alternativa).
Autenticación: JSON Web Tokens (JWT) para seguridad basada en roles.
Infraestructura: Despliegue en servidores en la nube (AWS o Azure) utilizando contenedores con Docker para mayor portabilidad.

⚙️ Entorno de Desarrollo y Herramientas

Para el ecosistema de Python y el trabajo colaborativo, se utilizarán las siguientes herramientas:
Gestión de dependencias: pip.
Pruebas y calidad: PyTest.
Control de versiones: Git con repositorio en GitHub.

🔄 Metodología y Flujo de Trabajo (GitFlow)

El desarrollo del proyecto se rige por la metodología ágil Scrum. Para mantener el orden en el repositorio, utilizamos la siguiente estructura de ramas:
main: Rama principal, contiene únicamente código estable y funcional (versiones de producción).
develop: Rama de integración donde se unen las funcionalidades completadas en los Sprints.
feature/nombre-funcionalidad: Ramas temporales creadas a partir de develop para trabajar en tareas específicas (ej. feature/login).
