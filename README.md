# Sistema de Control de Equipos Tecnológicos

Sistema web para la gestión y seguimiento del inventario de equipos tecnológicos dentro de una organización. Permite registrar, consultar, actualizar y dar de baja equipos (computadoras, impresoras, proyectores, etc.), así como controlar asignaciones a usuarios o departamentos.

---

## Tabla de Contenidos

- [Descripción del Proyecto](#descripción-del-proyecto)
- [Características](#características)
- [Tecnologías](#tecnologías)
- [Instalación](#instalación)
- [Guía de Uso](#guía-de-uso)
- [Estrategia de Ramas](#estrategia-de-ramas)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

---

## Descripción del Proyecto

El **Sistema de Control de Equipos Tecnológicos** centraliza la administración del inventario tecnológico de una empresa o institución. Facilita:

- El registro detallado de cada equipo (número de serie, marca, modelo, estado, fecha de adquisición).
- El seguimiento de asignaciones: qué equipo está asignado a qué usuario o área.
- La generación de reportes de inventario actualizados.
- El control del ciclo de vida de los equipos (activo, en mantenimiento, dado de baja).

---

## Características

- 📋 **Inventario completo**: Registro y consulta de equipos tecnológicos.
- 👤 **Asignación a usuarios**: Vinculación de equipos a personas o departamentos.
- 🔧 **Gestión de mantenimiento**: Control de equipos en reparación o servicio.
- 📊 **Reportes**: Generación de informes del estado del inventario.
- 🔒 **Control de acceso**: Roles diferenciados (administrador, consulta).

---

## Tecnologías

> _Las tecnologías específicas se definirán conforme avance el desarrollo._

- Lenguaje / Framework: _por definir_
- Base de datos: _por definir_
- Control de versiones: **Git / GitHub**

---

## Instalación

> _Las instrucciones detalladas de instalación se agregarán una vez que el stack tecnológico esté definido._

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/gAntoniog/Sistema-de-Control-de-Equipos-Tecnologicos.git
   cd Sistema-de-Control-de-Equipos-Tecnologicos
   ```
2. Instalar dependencias (cuando aplique):
   ```bash
   # ejemplo: npm install  /  pip install -r requirements.txt
   ```
3. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con los valores correspondientes
   ```
4. Ejecutar la aplicación:
   ```bash
   # ejemplo: npm start  /  python app.py
   ```

---

## Guía de Uso

### Registro de un equipo nuevo

1. Acceder al módulo **Inventario**.
2. Hacer clic en **Agregar equipo**.
3. Completar el formulario con los datos del equipo (tipo, marca, modelo, número de serie, fecha de adquisición, estado).
4. Guardar los cambios.

### Asignación de un equipo

1. Localizar el equipo en el listado de inventario.
2. Seleccionar la opción **Asignar**.
3. Buscar y seleccionar al usuario o departamento destinatario.
4. Confirmar la asignación.

### Generar un reporte

1. Ir al módulo **Reportes**.
2. Seleccionar los filtros deseados (estado, tipo de equipo, área, rango de fechas).
3. Hacer clic en **Generar reporte**.
4. Exportar en el formato requerido (PDF, Excel, etc.).

---

## Estrategia de Ramas

Este proyecto utiliza el siguiente flujo de trabajo con Git:

| Rama | Propósito |
|------|-----------|
| `main` | Código estable listo para producción. Solo recibe merges desde `develop` (o `hotfix/*`). |
| `develop` | Rama de integración y desarrollo activo. Las funcionalidades se integran aquí antes de pasar a `main`. |
| `feature/*` | Ramas de trabajo para nuevas funcionalidades. Se crean desde `develop` y se fusionan de vuelta a `develop` mediante Pull Request. |
| `hotfix/*` | Correcciones urgentes en producción. Se crean desde `main` y se fusionan tanto en `main` como en `develop`. |
| `release/*` | Preparación de una nueva versión. Se crean desde `develop` para ajustes finales antes del merge a `main`. |

### Convención de nombres

```
feature/nombre-de-la-funcionalidad   # nueva funcionalidad
hotfix/descripcion-del-error         # corrección urgente en producción
release/v1.0.0                       # preparación de release
```

### Flujo de trabajo típico

```bash
# Crear una nueva funcionalidad
git checkout develop
git pull origin develop
git checkout -b feature/nombre-funcionalidad

# ... realizar cambios y commits ...

# Publicar la rama y abrir un Pull Request hacia develop
git push origin feature/nombre-funcionalidad
```

---

## Contribuir

1. Hacer **fork** del repositorio.
2. Crear una rama de funcionalidad siguiendo la convención: `feature/mi-funcionalidad`.
3. Realizar los cambios y hacer commits con mensajes descriptivos.
4. Abrir un **Pull Request** hacia la rama `develop` con una descripción clara de los cambios.
5. Esperar la revisión y aprobación antes del merge.

---

## Licencia

Este proyecto se encuentra bajo la licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
