import pandas as pd
import numpy as np
import os
import warnings
from datetime import datetime
from config_db import obtener_conexion

# 1. Configuración de Entorno
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

def obtener_query(mes):
    """Lee el SQL maestro y reemplaza el parámetro del mes."""
    dir_path = os.path.dirname(os.path.abspath(__file__))
    ruta_sql = os.path.join(dir_path, 'consumos.sql')
    
    if not os.path.exists(ruta_sql):
        raise FileNotFoundError(f"⚠️ No se encontró el archivo SQL en: {ruta_sql}")
        
    with open(ruta_sql, 'r', encoding='utf-8') as f:
        query = f.read()
    
    # Reemplazo seguro de variable
    return query.replace("{mes_analisis}", str(mes))

def ejecutar_analisis_maestro(mes_objetivo):
    start_time = datetime.now()
    print(f"🚀 [{start_time.strftime('%H:%M:%S')}] Iniciando Extracción General: Mes {mes_objetivo}")
    
    try:
        # 2. Extracción de Datos desde Impala
        query = obtener_query(mes_objetivo)
        with obtener_conexion() as conn:
            df = pd.read_sql(query, conn)
        
        if df is None or df.empty:
            print("⚠️ La consulta no devolvió datos. Revisa los filtros en el SQL.")
            return

        print(f"✅ Datos cargados: {len(df):,} registros.")

        # 3. Limpieza y Preparación de Métricas
        # Convertimos a numérico por si Impala devuelve strings y llenamos Nulos
        cols_metricas = ['consumo_mb', 'huella_mb', 'monto_bolsa_mb']
        for col in cols_metricas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 4. CÁLCULO DE PERCENTILES (De lo General...)
        # Solo calculamos percentiles sobre usuarios que efectivamente tuvieron tráfico > 0
        df_activos = df[df['consumo_mb'] > 0.01].copy()
        
        if not df_activos.empty:
            print("📊 Calculando distribución de Deciles (P10 - P100)...")
            # Creamos 10 grupos de igual tamaño
            df_activos['percentil_general'] = pd.qcut(
                df_activos['consumo_mb'], 
                q=10, 
                labels=[f'P{i*10}' for i in range(1, 11)],
                duplicates='drop'
            )
        else:
            print("⚠️ No hay consumos mayores a 0 para calcular percentiles.")
            df_activos = df.copy()
            df_activos['percentil_general'] = 'Sin Consumo'

        # 5. EXTRACCIÓN DE CAPACIDADES (...A lo Particular)
        # Extraemos la navegación base del product_name usando Regex (Nomenclatura WIMO)
        # Ejemplo: '... 1638+410M ...' extrae 1638
        df_activos['capacidad_oferta_mb'] = df_activos['product_name'].str.extract(r'(\d+)\+\d+M').astype(float)

        # 6. GENERACIÓN DE REPORTES
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        # Reporte A: Resumen de Distribución Estadística
        resumen_dist = df_activos.groupby('percentil_general').agg({
            'msisdn': 'nunique',
            'consumo_mb': ['min', 'mean', 'max', 'sum'],
            'huella_mb': 'sum'
        }).reset_index()
        
        # Aplanamos el multi-index de las columnas
        resumen_dist.columns = ['Decil', 'Q_Usuarios', 'Min_MB', 'Avg_MB', 'Max_MB', 'Total_Consumo_MB', 'Total_Huella_MB']
        
        # Guardar Archivos
        nombre_resumen = f"Distribucion_General_{mes_objetivo}_{timestamp}.csv"
        nombre_cubo = f"Cubo_Maestro_Consumos_{mes_objetivo}.csv"
        
        resumen_dist.to_csv(nombre_resumen, index=False, encoding='utf-8-sig')
        # Guardamos el cubo completo (etiquetado) para que hagas tus cruces en Excel/PowerBI
        df_activos.to_csv(nombre_cubo, index=False, encoding='utf-8-sig')

        end_time = datetime.now()
        duracion = end_time - start_time
        print(f"✨ Proceso terminado en {duracion.seconds} segundos.")
        print(f"📂 Reporte de Deciles: {nombre_resumen}")
        print(f"📂 Cubo Completo (para análisis WIMO): {nombre_cubo}")
        
        return df_activos

    except Exception as e:
        print(f"❌ Error crítico en el script: {str(e)}")

if __name__ == "__main__":
    # Ejecución para Marzo 2026
    ejecutar_analisis_maestro(202603)