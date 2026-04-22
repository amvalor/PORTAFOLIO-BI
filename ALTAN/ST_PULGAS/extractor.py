import pandas as pd
import sys
from config_db import obtener_conexion

class ExtractorPulgas:
    """
    Clase encargada de la extracción y almacenamiento en memoria
    del universo de datos de Portabilidad.
    """
    def __init__(self):
        self.df_raw = None
        self.estado = "PENDIENTE"
        self.error_msg = ""

    def obtener_query(self):
        return """
        SELECT 
            apigw_transaction_id
            , load_processing_hour
            , be_id
            , transaction_timestamp_fmt
            , msisdn_ported
            , window_abd_date_fmt
            , operation
            , imsi
            , msisdn_backup
            , dida
            , dcr
            , rida
            , rcr
            , transaction_result
            , transaction_detail
            , comments
            , load_processing_timestamp
            , auto_expiration
        FROM bss.portability_logs
        WHERE CAST(load_processing_hour/10000 AS INT) >= (SELECT CAST(FROM_TIMESTAMP(NOW() - INTERVAL 3 MONTH, 'yyyyMM') AS INT))
        """

    def ejecutar_extraccion(self):
        query = self.obtener_query()
        print("\n" + "█"*115)
        print("\nIniciando extracción de datos...")
        
        try:
            # 1. Intento de Conexión (Error Crítico 1)
            conn = obtener_conexion()
            if not conn:
                raise ConnectionError("No se pudo establecer el túnel con la base de datos.")
            
            # 2. Lectura de Datos
            # Nota: Podríamos implementar un timer aquí para el Error Crítico 3 (Lentitud)
            self.df_raw = pd.read_sql(query, conn)
            conn.close()

            # 3. Validación de contenido (Error Crítico 2)
            if self.df_raw is None or self.df_raw.empty:
                self.estado = "CRITICAL_ERROR"
                print("❌ ERROR CRÍTICO: Tabla vacía o sin registros para el periodo.")
                sys.exit(1) # Detención total del proceso

            # Normalización mínima necesaria para el almacenamiento
            self.df_raw['operation'] = self.df_raw['operation'].str.strip().str.upper()
            self.df_raw['transaction_result'] = self.df_raw['transaction_result'].astype(str).str.strip()
            
            self.estado = "SUCCESS"
            print(f"✅ Extracción completada: {len(self.df_raw):,} registros en memoria.")
            print("\n" + "█"*115)
            return self.df_raw

        except Exception as e:
            self.estado = "CRITICAL_ERROR"
            print(f"❌ FALLO CRÍTICO EN EL SISTEMA: {str(e)}")
            sys.exit(1) # Detención total por integridad

# Instancia global para ser invocada por otros módulos
# Esto mantiene los datos 'vivos' en el proceso actual
data_manager = ExtractorPulgas()