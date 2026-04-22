import pandas as pd

class ReporteGeneralPulgas:
    """
    Clase para generar métricas de volumen de portabilidad 
    basadas en datos previamente limpiados.
    """
    def __init__(self, df_limpio):
        if df_limpio is None or df_limpio.empty:
            raise ValueError("No hay datos limpios disponibles para reportar.")
        self.df = df_limpio

    def obtener_totales_portabilidad(self):
        """
        Calcula los totales de Port-In y Port-Out segmentados por mes.
        Considera solo las operaciones core de portabilidad.
        """
        # Definimos las operaciones que nos interesan para este análisis general
        ops_interes = ['PORTABILIDAD IN C', 'PORTABILIDAD OUT C', 'ACTIVACION DE PORTABILIDAD']
        
        df_filtrado = self.df[self.df['operation'].isin(ops_interes)]
        
        # Agrupamos por mes y operación
        reporte = df_filtrado.groupby(['mes_analisis', 'operation']).agg(
            registros_validos=('apigw_transaction_id', 'count'),
            usuarios_unicos=('msisdn_ported', 'nunique')
        ).reset_index()
        
        return reporte

    def imprimir_dashboard_consola(self, reporte):
        """Presenta los resultados en un formato de tabla profesional."""
        print("\n" + "="*65)
        print(f"{'REPORTE GENERAL DE PORTABILIDAD (FLAG 200)':^65}")
        print("="*65)
        print(f"{'MES':<10} | {'OPERACIÓN':<28} | {'REGS':<10} | {'UNICOS'}")
        print("-" * 65)
        
        for _, row in reporte.iterrows():
            print(f"{row['mes_analisis']:<10} | {row['operation']:<28} | {row['registros_validos']:<10,} | {row['usuarios_unicos']:<10,}")
            
        print("-" * 65)
        print(f"Total registros analizados: {reporte['registros_validos'].sum():,}")
        print("="*65 + "\n")

# --- Lógica de Integración ---
# Este bloque simula cómo llamarías a los módulos en tu archivo principal:
# from extractor import data_manager
# from limpiador import LimpiadorPulgas

# 1. Extraer
# df_raw = data_manager.ejecutar_extraccion()
# 2. Limpiar
# df_clean = LimpiadorPulgas(df_raw).normalizar_formatos().filtrar_exitos_reales().obtener_datos_limpios()
# 3. Reportar
# reporte_gen = ReporteGeneralPulgas(df_clean)
# totales = reporte_gen.obtener_totales_portabilidad()
# reporte_gen.imprimir_dashboard_consola(totales)