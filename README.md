# training-platform-mcp-g2

## Descripción

Este repositorio contiene el servidor MCP `Historial Cursos MCP`, construido con FastMCP/ffmcp en Python. Gestiona el progreso de cursos de usuarios autenticados mediante `go-token` y almacena los datos en SQL Server.

Carpeta principal del servidor: `mcp/`

## Requisitos

- Docker y Docker Compose instalados.
- Acceso a SQL Server o un contenedor MSSQL.
- Variables de entorno de conexión a la base de datos.
- `kubectl` configurado para despliegues en Kubernetes.

## Estructura relevante

- `mcp/Dockerfile`: define la imagen Docker del servidor.
- `mcp/docker-compose.yml`: despliegue local con Docker Compose.
- `mcp/mcp.yaml`: configuración del servidor MCP.
- `mcp/k8s-deployment.yaml`: manifiesto Kubernetes (Deployment, Service, Ingress).
- `mcp/k8s-db-secret.yaml`: secreto Kubernetes para credenciales de SQL Server.
- `mcp/Creación de base de datos.sql`: script de creación de tablas.
- `mcp/main.py`: entrypoint del servidor.
- `mcp/db.py`: helper para conexión y acceso a la base de datos.
- `mcp/namespaces/gestion_historial/handlers.py`: define las tools, recurso y prompt.
- `mcp/namespaces/gestion_historial/config.py`: configuración del namespace.
- `mcp/namespaces/gestion_historial/auth.py`: validación del token GO.

## Instalación local con Docker Compose

### 1. Preparar el entorno

En la raíz del repositorio, ve a la carpeta `mcp`:

```bash
cd mcp
```

### 2. Crear archivo .env

Crea un archivo `.env` junto a `docker-compose.yml` con los siguientes valores:

```env
NEXUS_USER=<tu_usuario_nexus>
NEXUS_PASSWORD=<tu_password_nexus>
DB_HOST=<host_sql_server>
DB_PORT=1433
DB_USER=<usuario_sql>
DB_PASSWORD=<password_sql>
DB_NAME=HistorialCursos
```

### 3. Construir y ejecutar

```bash
docker compose up --build
```

### 4. Verificar

Abre `http://localhost:8000` para verificar que el servidor esté disponible.

> El servidor carga `mcp/mcp.yaml` y expone el puerto `8000`.

## Inicialización de base de datos SQL Server

Antes de arrancar el servidor, crea la base de datos y las tablas ejecutando:

```bash
sqlcmd -S <host>,1433 -U <usuario> -P <password> -i "mcp/Creación de base de datos.sql"
```

El script crea tres tablas:
- `courses`: catálogo de cursos
- `stages`: etapas del flujo de aprendizaje
- `student_progress`: registro de progreso del estudiante

## Variables de entorno

- `DB_HOST`: host del servidor SQL Server
- `DB_PORT`: puerto de SQL Server (por defecto 1433)
- `DB_USER`: usuario de SQL Server
- `DB_PASSWORD`: password de SQL Server
- `DB_NAME`: nombre de la base de datos
- `SERVER_HOST`: host del servidor MCP (por defecto `0.0.0.0`)
- `SERVER_PORT`: puerto del servidor MCP (por defecto `8000`)

## Arquitectura del servidor

El servidor arranca con `python main.py` y usa `uvicorn`.

En `mcp/main.py`, la aplicación MCP se crea con:
- `namespaces_dir="./namespaces"`
- `config_file="mcp.yaml"`

Esto carga automáticamente el namespace `gestion_historial` desde `mcp/namespaces/gestion_historial/`.

## Tools del MCP

### `get_course_progress`

Recupera el progreso actual del usuario autenticado.

**Funcionamiento:**
- Extrae el `access_token` del contexto MCP o del header `Authorization: Bearer <token>`
- Valida el token contra `https://go.finneg.com/auth/token/info`
- Consulta la base de datos y devuelve:
  - `user_email`: email del usuario
  - `current_course`: nombre del curso actual
  - `current_stage`: nombre de la etapa actual
  - `updated_at`: timestamp de la última actualización

**Ejemplo de respuesta:**
```json
{
  "user_email": "usuario@example.com",
  "current_course": "Programacion_desde_0_Parte_1",
  "current_stage": "ADELINA_TEORIA",
  "updated_at": "2026-06-17T10:30:45.123456"
}
```

### `save_course_progress`

Guarda o actualiza el progreso de curso del usuario autenticado.

**Parámetros:**
- `course_name` (string): nombre del curso
- `stage_name` (string): nombre de la etapa

**Funcionamiento:**
- Valida el token y obtiene el email del usuario
- Crea el curso en la tabla `courses` si no existe
- Crea la etapa en la tabla `stages` si no existe
- Inserta o actualiza el registro en `student_progress`

**Ejemplo de respuesta:**
```json
{
  "status": "ok",
  "user_email": "usuario@example.com",
  "saved_course": "Programacion_desde_0_Parte_1",
  "saved_stage": "ADELINA_TEORIA",
  "updated_at": "2026-06-17T10:30:45.123456"
}
```

