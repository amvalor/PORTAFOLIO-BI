
# PORTABILIDAD/actualizar_id_pos.py
import pandas as pd
import datetime
import warnings
import os
import unicodedata
import re  # Importamos Regex para limpieza profunda
from config_db import obtener_conexion

warnings.filterwarnings("ignore", category=UserWarning)

def limpiar_texto(texto, es_columna=False):
    """Limpia tildes, eñes y caracteres especiales prohibidos en SQL."""
    if pd.isna(texto) or not isinstance(texto, str):
        return texto
    
    # 1. Quitar tildes y normalizar
    texto_normalizado = unicodedata.normalize('NFD', texto)
    solo_base = "".join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    resultado = solo_base.replace('ñ', 'n').replace('Ñ', 'N').upper().strip()
    
    if es_columna:
        # 2. Limpieza agresiva para nombres de columnas (Solo A-Z, 0-9 y _)
        # Reemplaza cualquier cosa que NO sea letra o número por un espacio
        limpio = re.sub(r'[^A-Z0-9]', ' ', resultado)
        # Reemplaza espacios (uno o más) por un solo guion bajo
        return re.sub(r'\s+', '_', limpio).strip('_')
    
    return resultado

def ejecutar_actualizacion_id_pos():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    archivo_ruta = os.path.join(base_dir, 'CATALOGOS', 'CATALOGO_ID_POS.csv')
    tabla_destino = 'analysis_aftersale.amv_cat_id_pos'
    
    print(f"--- [INICIO] Actualizando: {tabla_destino} ---")
    
    if not os.path.exists(archivo_ruta):
        print(f"❌ Error: Archivo no encontrado en {archivo_ruta}")
        return

    try:
        # Lectura con detección de BOM
        try:
            df = pd.read_csv(archivo_ruta, encoding='utf-8-sig', sep=',', dtype=str)
        except:
            df = pd.read_csv(archivo_ruta, encoding='latin1', sep=',', dtype=str)

        # Limpiar ENCABEZADOS (Aquí eliminamos los paréntesis)
        df.columns = [limpiar_texto(col, es_columna=True) for col in df.columns]
        
        # Limpiar CONTENIDO
        for col in df.columns:
            df[col] = df[col].apply(lambda x: limpiar_texto(x) if isinstance(x, str) else x)
        
        df = df.dropna(how='all').drop_duplicates()
        
        fecha_actual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['FECHA_ACTUALIZACION'] = fecha_actual
        
        print(f"✅ Columnas limpias: {list(df.columns)}")
        print(f"✅ Registros listos: {len(df)}")

        conn = obtener_conexion()
        if conn:
            cursor = conn.cursor()
            
            print(f"🗑️ Recreando tabla {tabla_destino}...")
            cursor.execute(f"DROP TABLE IF EXISTS {tabla_destino}")
            
            columnas_def = " , ".join([f"`{col}` STRING" for col in df.columns])
            sql_create = f"CREATE TABLE {tabla_destino} ({columnas_def}) STORED AS PARQUET"
            cursor.execute(sql_create)
            
            columnas_lista = ", ".join([f"`{col}`" for col in df.columns])
            placeholders = ", ".join(["?"] * len(df.columns))
            sql_insert = f"INSERT INTO {tabla_destino} ({columnas_lista}) VALUES ({placeholders})"
            
            print(f"🚀 Cargando datos...")
            datos_tuplas = [tuple(x) for x in df.values]
            cursor.executemany(sql_insert, datos_tuplas)
            
            conn.commit()
            print(f"✨ ¡ÉXITO! Catálogo ID_POS actualizado a las {fecha_actual}")
            
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"❌ Error durante el proceso de ID_POS: {e}")

if __name__ == "__main__":
    ejecutar_actualizacion_id_pos()