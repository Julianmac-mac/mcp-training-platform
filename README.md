# Training Platform MCP G2

## ¿Qué hace este proyecto?

Este repositorio contiene un servidor MCP (Model Context Protocol) en Python para registrar y consultar el progreso de cursos de usuarios autenticados. Expone herramientas como `get_course_progress` y `save_course_progress`, valida tokens de acceso y persiste la información en SQL Server.

## Estructura principal

- `main.py`: punto de entrada del servidor MCP.
- `mcp.yaml`: configuración del servidor y del namespace registrado.
- `db.py`: conexión a SQL Server y operaciones de progreso.
- `db_init.sql`: script SQL para crear la estructura base.
- `init_db.py`: inicializa la base de datos localmente.
- `docker-compose.yml`: levanta la aplicación y SQL Server para desarrollo.
- `namespaces/training_platform_mcp_g2/handlers.py`: define las herramientas, recursos y prompt del namespace.
- `namespaces/training_platform_mcp_g2/auth.py`: extrae y valida el token del usuario.
- `namespaces/training_platform_mcp_g2/config.py`: configura el namespace del MCP.

## Requisitos

- Python 3.10+
- Docker y Docker Compose (opcional, pero recomendado)
- SQL Server o un contenedor local
- Variables de entorno para la conexión a la base de datos

## Configuración rápida

1. Copia `.env.example` a `.env` y ajusta los valores.
2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

3. Inicia el servidor:

```bash
python main.py
```

4. Si prefieres usar Docker Compose:

```bash
docker compose up --build
```

## Variables de entorno importantes

- `DB_HOST`: host del servidor SQL Server
- `DB_PORT`: puerto de SQL Server
- `DB_USER`: usuario de base de datos
- `DB_PASSWORD`: contraseña de base de datos
- `DB_NAME`: nombre de la base de datos
- `GO_BASE_PATH`: base para validar tokens
- `SERVER_HOST` y `SERVER_PORT`: configuración del servidor MCP

## Herramientas expuestas

### `get_course_progress`
Recupera el curso y la etapa actual del usuario autenticado.

### `save_course_progress`
Guarda o actualiza el progreso del usuario autenticado.

## Notas para revisar el proyecto

El código está organizado por responsabilidad: entrada del servidor, configuración del namespace, lógica de autenticación y acceso a datos. Para que sea fácil de revisar, conviene mantener el README actualizado, los secretos fuera del repositorio y los ejemplos de entorno en `.env.example`.

