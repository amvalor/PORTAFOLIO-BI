import pandas as pd
import numpy as np

class LimpiadorPulgas:
    """
    Clase encargada de transformar los datos brutos en información 
    conduciva para el análisis de portabilidad.
    """
    def __init__(self, df_input):
        if df_input is None or df_input.empty:
            raise ValueError("El DataFrame de entrada está vacío. No se puede limpiar.")
        self.df = df_input.copy()

    def normalizar_formatos(self):
        """Asegura consistencia en tipos de datos y strings."""
        # Normalizar Operaciones a Mayúsculas y sin espacios
        self.df['operation'] = self.df['operation'].str.strip().str.upper()
        
        # Asegurar que la Flag de resultado sea String para evitar errores de tipo mixto
        self.df['transaction_result'] = self.df['transaction_result'].astype(str).str.strip()
        
        # Conversión de Timestamps (si no vienen formateados)
        self.df['load_processing_timestamp'] = pd.to_datetime(self.df['load_processing_timestamp'])
        
        # Crear dimensión de tiempo para reporteo (Mes)
        self.df['mes_analisis'] = self.df['load_processing_timestamp'].dt.strftime('%Y-%m')
        return self

    def filtrar_exitos_reales(self):
        """Aplica la regla de negocio: Solo transacciones con código 200."""
        conteo_previo = len(self.df)
        self.df = self.df[self.df['transaction_result'] == '200']
        
        descarte = conteo_previo - len(self.df)
        print("\n" + "█"*115)
        print(f"{'INICIO DE LIMPIEZA':^115}")
        print(f"[CLEANING] Registros filtrados (No exitosos): {descarte:,}")
        print(f"[CLEANING] Registros válidos (Flag 200): {len(self.df):,}")
        return self

    def depurar_nulos_criticos(self):
        """Elimina registros que no tienen MSISDN, ya que son inservibles para el análisis."""
        nulos_msisdn = self.df['msisdn_ported'].isnull().sum()
        if nulos_msisdn > 0:
            self.df = self.df.dropna(subset=['msisdn_ported'])
            print(f"[CLEANING] MSISDNs nulos eliminados: {nulos_msisdn}")
        return self

    def obtener_datos_limpios(self):
        """Retorna el DataFrame final listo para el siguiente eslabón."""
        print("✅ Proceso de limpieza completado con éxito.")
        print("\n" + "█"*115)
        return self.df

# Ejemplo de integración lógica:
# limpiador = LimpiadorPulgas(df_extraido)
# df_limpio = limpiador.normalizar_formatos().filtrar_exitos_reales().depurar_nulos_criticos().obtener_datos_limpios()