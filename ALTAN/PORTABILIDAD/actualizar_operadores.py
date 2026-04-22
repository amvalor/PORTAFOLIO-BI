# PORTABILIDAD/actualizar_operadores.py
import pandas as pd
import datetime
import warnings
import os
import unicodedata
from config_db import obtener_conexion

warnings.filterwarnings("ignore", category=UserWarning)

def limpiar_texto(texto):
    """Limpia tildes, eñes, espacios y caracteres invisibles."""
    if pd.isna(texto) or not isinstance(texto, str):
        return texto
    # Eliminar el BOM (Ã¯Â»Â¿) y normalizar
    texto = texto.encode('ascii', 'ignore').decode('ascii') if 'Ã¯' in texto else texto
    texto_normalizado = unicodedata.normalize('NFD', texto)
    solo_base = "".join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    return solo_base.replace('ñ', 'n').replace('Ñ', 'N').upper().strip().replace(" ", "_")

def ejecutar_actualizacion_operadores():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    archivo_ruta = os.path.join(base_dir, 'CATALOGOS', 'CATALOGO_OPERADORES.csv')
    tabla_destino = 'analysis_aftersale.amv_cat_operadores'
    
    print(f"--- [INICIO] Actualizando Catálogo de Operadores ---")
    
    if not os.path.exists(archivo_ruta):
        print(f"❌ Error: No se encuentra el archivo en {archivo_ruta}")
        return

    try:
        # 1. LECTURA CON ELIMINACIÓN DE BOM (utf-8-sig)
        try:
            df = pd.read_csv(archivo_ruta, encoding='utf-8-sig', sep=',', dtype=str)
        except:
            df = pd.read_csv(archivo_ruta, encoding='latin1', sep=',', dtype=str)

        # 2. LIMPIEZA PROFESIONAL
        # Limpiar nombres de columnas (importante para evitar el error de 'id tienda')
        df.columns = [limpiar_texto(col) for col in df.columns]
        
        # Limpiar contenido de las celdas
        for col in df.columns:
            df[col] = df[col].apply(limpiar_texto)
        
        df = df.dropna(how='all').drop_duplicates()
        
        # Sello de auditoría
        fecha_actual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['FECHA_ACTUALIZACION'] = fecha_actual
        
        print(f"✅ Datos listos: {len(df)} registros detectados.")

        # 3. CONEXIÓN E INSERCIÓN (Drop & Create)
        conn = obtener_conexion()
        if conn:
            cursor = conn.cursor()
            
            print(f"🗑️ Recreando tabla {tabla_destino}...")
            cursor.execute(f"DROP TABLE IF EXISTS {tabla_destino}")
            
            # Definición de columnas (Todas como STRING para evitar fallos de tipo)
            columnas_def = " , ".join([f"`{col}` STRING" for col in df.columns])
            sql_create = f"CREATE TABLE {tabla_destino} ({columnas_def}) STORED AS PARQUET"
            cursor.execute(sql_create)
            
            print(f"🚀 Insertando registros en Impala...")
            columnas_lista = ", ".join([f"`{col}`" for col in df.columns])
            placeholders = ", ".join(["?"] * len(df.columns))
            sql_insert = f"INSERT INTO {tabla_destino} ({columnas_lista}) VALUES ({placeholders})"
            
            datos_tuplas = [tuple(x) for x in df.values]
            cursor.executemany(sql_insert, datos_tuplas)
            
            conn.commit()
            print(f"✨ ¡ÉXITO! Catálogo de Operadores actualizado a las {fecha_actual}")
            
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"❌ Error en el proceso: {e}")

if __name__ == "__main__":
    ejecutar_actualizacion_operadores()