import time
import pyodbc

# Credenciales hardcodeadas por fines practicos
host = "localhost"
port = "1433"
username = "sa"
password = "Clave_2019!"
server_address = f"{host},{port}"

# Nos conectamos a 'master' para poder dropear y crear la base
conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server_address};DATABASE=master;UID={username};PWD={password};TrustServerCertificate=yes;"

print("Esperando a que SQL Server este listo...")
conn = None
for _ in range(30):
    try:
        # Autocommit = True es requerido para ejecutar CREATE DATABASE
        conn = pyodbc.connect(conn_str, autocommit=True)
        break
    except Exception as e:
        time.sleep(2)

if not conn:
    print("No se pudo conectar a SQL Server.")
    exit(1)

print("Conexion exitosa. Ejecutando script de inicializacion...")
cursor = conn.cursor()

try:
    with open('db_init.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # pyodbc no soporta 'GO', tenemos que separar por lotes
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
