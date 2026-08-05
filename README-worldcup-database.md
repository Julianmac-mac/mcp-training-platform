# World Cup Database

Proyecto de la certificación **Relational Databases** de freeCodeCamp. Consiste en modelar y poblar una base de datos PostgreSQL con resultados de partidos de los Mundiales 2014 y 2018, usando Bash para automatizar tanto la carga de datos como las consultas.

## ¿Qué hace?

1. **Modela** dos tablas relacionadas (`teams` y `games`), con claves primarias, una restricción `UNIQUE` sobre el nombre de equipo, y dos claves foráneas en `games` que referencian a `teams` (equipo ganador y equipo perdedor).
2. **Carga los datos** desde `games.csv` (33 filas: encabezado + 32 partidos) mediante un script Bash que:
   - lee el CSV línea por línea,
   - inserta cada equipo en `teams` solo si todavía no existe (evita duplicados),
   - inserta cada partido en `games` con las claves foráneas correspondientes a ganador y perdedor.
3. **Consulta los datos** con un segundo script Bash que corre 11 queries: sumas y promedios de goles, máximos, conteos con `WHERE`, joins entre `teams` y `games`, `DISTINCT`, `ORDER BY` y filtros con `ILIKE`.

## Estructura de archivos

| Archivo | Qué es |
|---|---|
| `worldcup.sql` | Dump de PostgreSQL: define las tablas `teams` y `games` (con sus PK/FK) y su contenido ya cargado. |
| `games.csv` | Datos crudos de partidos (año, ronda, ganador, perdedor, goles). |
| `insert_data.sh` | Script Bash que parsea `games.csv` y puebla `teams` y `games`. |
| `queries.sh` | Script Bash con las 11 consultas de agregación y joins sobre la base. |
| `expected_output.txt` | Salida esperada de `queries.sh`, usada como referencia para validar el resultado. |

## Cómo correrlo

Requiere PostgreSQL con una base `worldcup` y un usuario `freecodecamp` con permisos sobre ella (o se puede adaptar la variable `PSQL` de cada script a tu propio usuario/base).

```bash
# 1. Crear el esquema
psql --username=freecodecamp --dbname=worldcup -f worldcup.sql

# 2. Cargar los datos desde el CSV
./insert_data.sh

# 3. Correr las consultas
./queries.sh
```

## Créditos

Proyecto guiado, desarrollado como parte del curso **Learn SQL by Building a World Cup Database** de la certificación [Relational Databases de freeCodeCamp](https://www.freecodecamp.org/learn/relational-databases-v9).
