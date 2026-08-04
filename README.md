# Training Platform MCP G2

## ¿Qué hace este proyecto?

Este repositorio contiene un servidor MCP (Model Context Protocol) en Python para registrar y consultar el progreso de cursos de usuarios autenticados. El servidor expone herramientas para:

- obtener el progreso actual de un usuario (`get_course_progress`)
- guardar el avance de curso y etapa (`save_course_progress`)

La aplicación valida tokens de acceso y persiste los datos en SQL Server.

## Estructura principal

- `main.py`: punto de entrada del servidor MCP.
- `mcp.yaml`: configuración del servidor y namespace.
- `db.py`: conexión y operaciones con SQL Server.
- `db_init.sql`: script SQL para crear la estructura de base de datos.
- `init_db.py`: script de inicialización local de la base de datos.
- `docker-compose.yml`: configuración de desarrollo con Docker Compose.
- `namespaces/training_platform_mcp_g2/handlers.py`: tools, recurso y prompt del namespace.
- `namespaces/training_platform_mcp_g2/auth.py`: extracción y validación del token.
- `namespaces/training_platform_mcp_g2/config.py`: definición del namespace.

## Requisitos

- Python 3.10+
- Docker y Docker Compose (opcional)
- SQL Server (local o remoto)
- Variables de entorno correctamente configuradas

## Configuración rápida

1. Copia `.env.example` a `.env`:

```bash
copy .env.example .env
```

2. Ajusta las variables:

```env
DB_HOST=<host_sql_server>
DB_PORT=1433
DB_USER=<usuario_sql>
DB_PASSWORD=<password_sql>
DB_NAME=HistorialCursos
SA_PASSWORD=<password_sql_server>
GO_BASE_PATH=<go_base_path>
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Inicia el servidor directamente:

```bash
python main.py
```

5. O usa Docker Compose:

```bash
docker compose up --build
```

Docker Compose cargará las variables desde el archivo `.env`.

## Variables de entorno importantes

- `DB_HOST`: host del servidor SQL Server
- `DB_PORT`: puerto de SQL Server
- `DB_USER`: usuario de SQL Server
- `DB_PASSWORD`: contraseña de SQL Server
- `DB_NAME`: nombre de la base de datos
- `SA_PASSWORD`: contraseña del usuario `sa` para SQL Server (solo Docker Compose)
- `GO_BASE_PATH`: URL base para validar tokens
- `SERVER_HOST`: host del servidor MCP
- `SERVER_PORT`: puerto del servidor MCP

## Inicialización de la base de datos

El proyecto incluye el script [db_init.sql](db_init.sql) para crear la base de datos y las tablas necesarias.

### Opción 1: usar Docker Compose
Si levantás el stack con Docker Compose, el contenedor de SQL Server se inicializa con el script incluido y queda listo para el servidor MCP.

### Opción 2: inicializarla manualmente
Si ya tenés SQL Server corriendo, podés ejecutar el script desde una herramienta como `sqlcmd` o desde tu cliente SQL Server:

```bash
sqlcmd -S <host> -U <usuario> -P <password> -i db_init.sql
```

El script crea:
- `courses`: catálogo de cursos
- `stages`: etapas del flujo de aprendizaje
- `student_progress`: registro del progreso de cada usuario

## Uso básico

### `get_course_progress`
Recupera el curso y la etapa actuales del usuario autenticado.

### `save_course_progress`
Guarda o actualiza el progreso de un usuario autenticado.

## Buenas prácticas para revisión

- No subir archivos de configuración local ni secretos.
- Mantener `pip.conf`, `.env` y `venv/` fuera del repositorio.
- Usar `.env.example` como plantilla de configuración.
- Documentar los endpoints o tools disponibles.

## Notas de seguridad

Este proyecto ya está configurado para leer la conexión a la base de datos desde variables de entorno en lugar de valores hardcodeados.

No debes subir nunca:

- `.env`
- `pip.conf`
- `pip.config`
- `venv/` o `.venv/`
- archivos con contraseñas, certificados o claves privadas

