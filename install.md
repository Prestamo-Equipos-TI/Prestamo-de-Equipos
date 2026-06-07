# Guía de Instalación - Control IT

## 📋 Requisitos Previos

### 1. Python 3.12.10
El proyecto requiere Python 3.12.10 (especificado en `runtime.txt`).

**Windows:**
```powershell
# Opción A: winget (requiere PowerShell como administrador)
winget install Python.Python.3.12

# Opción B: Chocolatey
choco install python --version=3.12.10

# Opción C: Descargar desde python.org
# https://www.python.org/downloads/release/python-31210/
# ✅ IMPORTANTE: Marcar "Add Python to PATH" durante la instalación
```

**Linux/macOS:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.12 python3.12-venv

# macOS (Homebrew)
brew install python@3.12

# Usando pyenv (recomendado para múltiples versiones)
pyenv install 3.12.10
pyenv local 3.12.10
```

### 2. PostgreSQL (Base de Datos)
El proyecto usa PostgreSQL con `psycopg2-binary`. 

**Windows:**
- Descargar instalador: https://www.postgresql.org/download/windows/
- O usar Docker: `docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:16`

**Linux:**
```bash
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql@16
brew services start postgresql@16
```

### 3. Git
```bash
# Windows: https://git-scm.com/download/win
# Linux: sudo apt install git
# macOS: brew install git
```

---

## 🚀 Instalación del Proyecto

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Prestamo-Equipos-TI/Prestamo-de-Equipos.git
cd Prestamo-de-Equipos
```

### 2. Crear Entorno Virtual
```bash
# Windows (PowerShell/CMD)
python -m venv venv
venv\Scripts\activate

# Linux/macOS (bash/zsh)
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
# Instalar requirements
pip install -r requirements.txt

# Actualizar pip. Solo si es necesario
pip install --upgrade pip
```

### 4. Configurar Variables de Entorno
Copiar el archivo de exemplo y editarlo:

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar el archivo .env con tus valores
# Windows (PowerShell):
notepad .env
# Linux/macOS:
nano .env
```

El archivo `.env.example` contiene todas las variables necesarias con valores de ejemplo. Debes completar al menos:

- `SECRET_KEY`: Generar una clave segura (ver comando abajo)
- `DATABASE_URL`: Tu conexión a PostgreSQL
- `DEBUG`: `True` para desarrollo, `False` para producción
- `ALLOWED_HOSTS`: Hosts permitidos (ej: `localhost,127.0.0.1`)

**Generar SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_string; print(get_random_string(50))"
```

### 5. Configurar Base de Datos PostgreSQL

Crear base de datos y usuario:
```sql
-- Conectar como postgres
psql -U postgres

-- En psql:
CREATE DATABASE control_it_db;
CREATE USER control_it_user WITH PASSWORD 'tu_password_seguro';
ALTER ROLE control_it_user SET client_encoding TO 'utf8';
ALTER ROLE control_it_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE control_it_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE control_it_db TO control_it_user;
\q
```

Actualizar `.env` con las credenciales:
```
DATABASE_URL=postgres://control_it_user:tu_password_seguro@localhost:5432/control_it_db
```

### 6. Ejecutar Migraciones
```bash
python manage.py migrate
```

### 7. Crear Superusuario (Admin)
```bash
python manage.py createsuperuser
# Seguir prompts: username, email, password
```

### 8. Cargar Datos Iniciales (Opcional)
```bash
# Si existe datos.json con fixtures
python manage.py loaddata datos.json
```

### 9. Recopilar Archivos Estáticos
```bash
python manage.py collectstatic --noinput
```

### 10. Iniciar Servidor de Desarrollo
```bash
python manage.py runserver
```

El proyecto estará disponible en: **http://127.0.0.1:8000/**

---

## 🐳 Alternativa: Docker (Recomendado para Producción)

### Dockerfile (crear si no existe)
```dockerfile
# Dockerfile
FROM python:3.12.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: control_it_db
      POSTGRES_USER: control_it_user
      POSTGRES_PASSWORD: tu_password_seguro
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://control_it_user:tu_password_seguro@db:5432/control_it_db
      - SECRET_KEY=tu-secret-key-aqui
      - DEBUG=False
      - ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
    depends_on:
      - db

volumes:
  postgres_data:
```

### Ejecutar con Docker
```bash
# Construir e iniciar
docker-compose up --build -d

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Ver logs
docker-compose logs -f web
```

---

## 🧪 Comandos Útiles

```bash
# Ejecutar tests
python manage.py test

# Ejecutar tests con coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report

# Shell de Django
python manage.py shell

# Ver migraciones pendientes
python manage.py showmigrations

# Crear migraciones tras cambios en modelos
python manage.py makemigrations

# Resetear base de datos (¡CUIDADO!)
python manage.py flush --noinput

# Cambiar contraseña de usuario
python manage.py changepassword username

# Ejecutar en otro puerto
python manage.py runserver 8080

# Acceder desde red local
python manage.py runserver 0.0.0.0:8000
```

---

## 📁 Estructura del Proyecto

```
Prestamo-de-Equipos/
├── config/                 # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── alertas/                # App alertas/notificaciones
├── averias/                # App gestión de averías
├── historial/              # App historial de movimientos
├── inventario/             # App inventario de equipos
├── prestamos/              # App préstamos
├── usuarios/               # App usuarios/autenticación
├── static/                 # Archivos estáticos (CSS, JS, imágenes)
├── staticfiles/            # Archivos estáticos recopilados
├── templates/              # Plantillas base
├── manage.py
├── requirements.txt
├── runtime.txt
├── .env                    # Variables de entorno (crear manualmente)
└── README.md
```

---

## 🔧 Solución de Problemas Comunes

### Error: "ModuleNotFoundError: No module named 'django'"
```bash
# Verificar entorno virtual activado
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

### Error: "django.db.utils.OperationalError: could not connect to server"
- Verificar que PostgreSQL esté corriendo
- Verificar credenciales en `.env` (DATABASE_URL)
- Verificar que la base de datos exista

### Error: "SECRET_KEY not found"
- Crear archivo `.env` con SECRET_KEY
- Verificar que python-decouple esté instalado

### Error: "Port 8000 already in use"
```bash
# Matar proceso en puerto 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8000 | xargs kill -9

# O usar otro puerto
python manage.py runserver 8080
```

### Error de migraciones
```bash
# Resetear migraciones (solo desarrollo)
rm -rf */migrations/00*.py
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

---

## 📝 Variables de Entorno Requeridas

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SECRET_KEY` | Clave secreta Django (50 chars) | `django-insecure-xyz...` |
| `DEBUG` | Modo debug | `True` / `False` |
| `ALLOWED_HOSTS` | Hosts permitidos | `localhost,127.0.0.1` |
| `DATABASE_URL` | URL conexión BD | `postgres://user:pass@host:port/db` |

---

## 🚀 Despliegue en Producción

### Checklist Pre-Despliegue
- [ ] `DEBUG=False` en `.env`
- [ ] `SECRET_KEY` fuerte y única
- [ ] `ALLOWED_HOSTS` con dominio real
- [ ] Base de datos PostgreSQL configurada
- [ ] `python manage.py collectstatic` ejecutado
- [ ] HTTPS configurado (nginx + certbot)
- [ ] Gunicorn como servidor WSGI
- [ ] Variables de entorno seguras (no en repo)

### Ejemplo systemd service (Linux)
```ini
# /etc/systemd/system/control-it.service
[Unit]
Description=Control IT Django App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/control-it
Environment="PATH=/var/www/control-it/venv/bin"
EnvironmentFile=/var/www/control-it/.env
ExecStart=/var/www/control-it/venv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/var/www/control-it/control-it.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

---

## 📞 Soporte

Si encuentras problemas:
1. Revisar logs: `python manage.py runserver --verbosity=2`
2. Verificar que todos los requisitos estén instalados
3. Consultar Issues en GitHub: https://github.com/Prestamo-Equipos-TI/Prestamo-de-Equipos/issues