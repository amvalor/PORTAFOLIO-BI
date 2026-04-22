# PORTABILIDAD/test.py
import pandas as pd
import warnings
from config_db import obtener_conexion

# Limpieza de ruido en consola
warnings.filterwarnings("ignore", category=UserWarning)

def probar_consulta(query_sql, titulo="RESULTADOS DE PRUEBA"):
    """Función genérica para probar cualquier query rápidamente."""
    conn = obtener_conexion()
    
    if conn:
        try:
            print(f"\n🚀 Ejecutando: {titulo}...")
            df = pd.read_sql(query_sql, conn)
            
            if df.empty:
                print("⚠️ La consulta no devolvió registros.")
            else:
                print("-" * 50)
                # Mostramos los primeros 20 resultados para no saturar la pantalla
                print(df.head(20).to_string(index=False)) 
                print("-" * 50)
                print(f"✅ Total de filas obtenidas: {len(df)}")
                
        except Exception as e:
            print(f"❌ Error en el query: {e}")
        finally:
            conn.close()
    else:
        print("🛑 Sin conexión.")

if __name__ == "__main__":
    # --- AQUÍ PUEDES CAMBIAR TU QUERY PARA PROBAR COSAS NUEVAS ---
    sql_test = """
    SELECT 
        *
    FROM (
    SELECT 
        event_month
        , operation
        , COUNT(DISTINCT msisdn_ported) AS usuarios
    FROM ▀▀▀▀▀▀▀▀▀
    GROUP BY 1,2
    UNION
    SELECT 
        event_month
        , operation
        , COUNT(DISTINCT msisdn_ported) AS usuarios
    FROM ▀▀▀▀▀▀▀▀▀
    GROUP BY 1,2
    ) AS A
    ORDER BY 1 DESC
    """
    
    probar_consulta(sql_test, "REPORTE MENSUAL PORT")
