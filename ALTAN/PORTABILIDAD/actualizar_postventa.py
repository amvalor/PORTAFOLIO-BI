# PORTABILIDAD/actualizar_posventa.py
import pandas as pd
import datetime
import warnings
import os
import unicodedata
import re
from config_db import obtener_conexion

warnings.filterwarnings("ignore", category=UserWarning)

def limpiar_texto(texto, es_columna=False):
    """
    Sanea el texto para evitar errores de sintaxis en SQL y nulos fantasmas.
    Si 'es_columna' es True, prepara el nombre para ser un encabezado de tabla válido.
    """
    if pd.isna(texto) or str(texto).lower() == 'nan' or str(texto).strip() == '':
        return None 
    
    # Eliminación de acentos y caracteres especiales
    texto_str = str(texto).strip()
    texto_normalizado = unicodedata.normalize('NFD', texto_str)
    solo_base = "".join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    resultado = solo_base.replace('ñ', 'n').replace('Ñ', 'N').upper().strip()
    
    if es_columna:
        # Reemplaza cualquier cosa que no sea letra o número por guion bajo
        limpio = re.sub(r'[^A-Z0-9]', ' ', resultado)
        res = re.sub(r'\s+', '_', limpio).strip('_')
        return res
    
    return resultado

def ejecutar_actualizacion_posventa():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    archivo_ruta = os.path.join(base_dir, 'CATALOGOS\CATALOGO_POSTVENTA.csv')
    tabla_destino = "analysis_aftersale.amv_cat_postventa"

    if not os.path.exists(archivo_ruta):
        print(f"❌ Error: No se localizó el archivo en {archivo_ruta}")
        return

    try:
        # [LECTURA DINÁMICA]
        # Cargamos el archivo sin nombres de columna fijos. Todo entra como texto (str).
        print(f"📖 Analizando estructura del archivo CSV...")
        df = pd.read_csv(archivo_ruta, encoding='utf-8', dtype=str)
        
        # Eliminamos filas que no tengan ningún dato
        df.dropna(how='all', inplace=True)

        # [PROCESAMIENTO DE COLUMNAS NUEVAS O CAMBIADAS]
        # El script toma los encabezados actuales del CSV y los transforma en nombres SQL válidos
        columnas_originales = list(df.columns)
        df.columns = [limpiar_texto(col, es_columna=True) for col in df.columns]
        
        # [LIMPIEZA DE CONTENIDO]
        # Aplicamos la limpieza a cada celda para evitar que caracteres raros rompan el INSERT
        for col in df.columns:
            df[col] = df[col].apply(limpiar_texto)

        # Agregamos registro de auditoría
        df['FECHA_ACTUALIZACION'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"✅ Se detectaron {len(columnas_originales)} columnas en el CSV.")
        print(f"✅ Estructura final de la tabla: {list(df.columns)}")

        # [CARGA A BASE DE DATOS]
        conn = obtener_conexion()
        if conn:
            cursor = conn.cursor()
            
            # 1. Limpieza total de la tabla previa
            print(f"🗑️ Eliminando tabla anterior para actualizar esquema...")
            cursor.execute(f"DROP TABLE IF EXISTS {tabla_destino}")
            
            # 2. Creación dinámica de la tabla basada en las columnas encontradas
            # Definimos todas como STRING para asegurar que no haya fallos por tipos de datos
            columnas_def = " , ".join([f"`{col}` STRING" for col in df.columns])
            sql_create = f"CREATE TABLE {tabla_destino} ({columnas_def}) STORED AS PARQUET"
            
            print(f"🛠️ Creando nueva tabla con las columnas detectadas...")
            cursor.execute(sql_create)
            
            # 3. Inserción Masiva
            columnas_insert = ", ".join([f"`{col}`" for col in df.columns])
            placeholders = ", ".join(["?"] * len(df.columns))
            sql_insert = f"INSERT INTO {tabla_destino} ({columnas_insert}) VALUES ({placeholders})"
            
            # Convertimos el DataFrame a una lista de tuplas compatible con el driver SQL
            datos_limpios = df.where(pd.notnull(df), None).values.tolist()
            datos_tuplas = [tuple(x) for x in datos_limpios]
            
            print(f"🚀 Cargando {len(datos_tuplas)} registros...")
            cursor.executemany(sql_insert, datos_tuplas)
            
            conn.commit()
            print(f"✨ ¡Proceso completado! La tabla '{tabla_destino}' refleja ahora el CSV actual.")
            
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"❌ Fallo en la actualización: {str(e)}")

if __name__ == "__main__":
    ejecutar_actualizacion_posventa()