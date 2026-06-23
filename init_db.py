import time
import pymssql  # Cambiado de pyodbc a pymssql

print("Iniciando script de inicializacion de la base de datos...")
# Credenciales hardcodeadas por fines practicos
host = "mssql"
port = "1433"
username = "sa"
password = "Clave_2019!"

print("Esperando a que SQL Server este listo...")
conn = None
for _ in range(30):
    try:
        # En pymssql pasamos los parámetros directamente.
        # autocommit=True es requerido para ejecutar CREATE DATABASE.
        conn = pymssql.connect(
            server=host,
            port=port,
            user=username,
            password=password,
            database='master',
            autocommit=True
        )
        break
    except Exception as e:
        print(f"Error al conectar a SQL Server: {e}")
        time.sleep(2)

if not conn:
    print("No se pudo conectar a SQL Server.")
    exit(1)

print("Conexion exitosa. Ejecutando script de inicializacion...")
cursor = conn.cursor()

try:
    with open('db_init.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # pymssql tampoco soporta 'GO' de forma nativa, se mantiene la separación por lotes
    batches = [b.strip() for b in sql_script.split('GO') if b.strip()]
    
    for batch in batches:
        if batch:
            try:
                cursor.execute(batch)
            except Exception as ex:
                print(f"Error ejecutando bloque: {batch[:50]}... \nExcepcion: {ex}")
                
    print("Inicializacion de la base de datos completada con exito.")
except Exception as e:
    print(f"Error al inicializar la base de datos: {e}")
finally:
    conn.close()