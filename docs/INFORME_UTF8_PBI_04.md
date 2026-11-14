# PBI-04: diagnóstico y reparación de UTF-8

## Evidencia

- PostgreSQL `controlit_db`: `server_encoding=UTF8` y `client_encoding=UTF8` durante la conexión de diagnóstico. La base tenía 49 campos afectados en `alertas_alerta` (26 títulos y 23 mensajes) y 2 en `averias_reporteaveria.descripcion_falla`.
- El valor almacenado era U+FFFD (`�`), no solo un carácter mostrado mal por HTML. Los 51 campos coincidían **exactamente** con los mismos campos e IDs del fixture versionado `datos.json`, que también contenía U+FFFD. Los registros posteriores de alertas ya tenían acentos correctos. La causa demostrada para esas filas es el fixture ya dañado; el origen previo de ese archivo no se puede reconstruir con certeza.
- El código fuente Python, HTML, CSS y JavaScript analizado es UTF-8 válido y no contiene U+FFFD. La página base declara `<meta charset="UTF-8">`; Django entrega HTML/HTMX en UTF-8 y JSON conserva los textos Unicode. Las pruebas cubren creación, edición, listado, búsqueda, exportación Excel y PDF, HTML, HTMX y JSON con `áéíóúÁÉÍÓÚñÑü¿¡`.
- PostgreSQL todavía no tiene la columna `usuarios_perfilusuario.debe_cambiar_clave` añadida después de PBI-01; por ello el diagnóstico usó SQL de solo lectura sobre el esquema existente. No se aplicaron migraciones ajenas a PBI-04.

## Reparación aplicada

El 13/11/2026, tras autorización expresa del usuario, se ejecutó el [plan de 51 correcciones](REPARACIONES_UTF8_PBI_04.json) sobre PostgreSQL. Cada entrada especifica modelo, ID, campo, valor original exacto y valor corregido; el comando aborta todo si un valor cambió. `datos.json` también quedó corregido para evitar reintroducir esas mismas filas dañadas al cargar el fixture.

La simulación previa coincidió en 51/51 valores. Después de aplicar, los 51 campos coincidieron con el texto corregido y no quedó U+FFFD en títulos o mensajes de alertas ni en descripciones de averías. El respaldo original está fuera del repositorio en `C:\Users\ricardo\Desktop\CONTROL_IT_PBI04_respaldo_20261113_01.json` (51 entradas). La simulación de reversión pasó; **no se ejecutó la reversión**. El respaldo contiene datos de la aplicación y no debe añadirse a Git.

## Uso del comando

El comando usa la base configurada por `DATABASE_URL`. Sin `--aplicar` solo simula:

```powershell
python manage.py reparar_utf8 --plan docs\REPARACIONES_UTF8_PBI_04.json
```

Para aplicar un plan nuevo, usar `--aplicar --respaldo RUTA_ABSOLUTA`. El respaldo debe estar fuera del repositorio, en una carpeta existente, y el archivo no puede existir previamente. Solo se admiten los campos listados en `reparar_utf8.py`, entradas con U+FFFD y coincidencia exacta del valor anterior.

Para comprobar una posible reversión del cambio de esta sesión:

```powershell
python manage.py reparar_utf8 --revertir C:\Users\ricardo\Desktop\CONTROL_IT_PBI04_respaldo_20261113_01.json
```

Para ejecutarla se añadirían `--aplicar --registro-reversion RUTA_ABSOLUTA_NUEVA`. La reversión también exige coincidencia exacta de los valores actuales y registra el cambio en un archivo nuevo. **No ejecutarla** salvo que se decida deshacer esta reparación.
