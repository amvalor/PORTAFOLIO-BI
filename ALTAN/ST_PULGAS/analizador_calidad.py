import pandas as pd
import numpy as np

class AnalizadorCalidadPulgas:
    """
    Analiza la calidad técnica diferenciando entre flujos de Entrada (Port-In) 
    y flujos de Salida (Port-Out).
    """
    def __init__(self, df_raw):
        if df_raw is None or df_raw.empty:
            raise ValueError("No hay datos brutos para el análisis de calidad.")
        self.df = df_raw.copy()

    def generar_diagnostico_segmentado(self):
        # 1. Preparación de datos
        self.df['es_exito'] = self.df['transaction_result'] == '200'
        self.df['mes'] = pd.to_datetime(self.df['load_processing_timestamp']).dt.strftime('%Y-%m')
        
        # 2. Clasificación de Flujo
        # Agrupamos operaciones de entrada (incluyendo activación) y salida
        condiciones = [
            self.df['operation'].isin(['PORTABILIDAD IN C', 'ACTIVACION DE PORTABILIDAD']),
            self.df['operation'] == 'PORTABILIDAD OUT C'
        ]
        elecciones = ['PORT-IN', 'PORT-OUT']
        self.df['flujo'] = np.select(condiciones, elecciones, default='OTRO')

        # 3. Agrupación por Mes y Flujo
        diagnostico = self.df[self.df['flujo'] != 'OTRO'].groupby(['mes', 'flujo']).agg(
            total_trans=('apigw_transaction_id', 'count'),
            exitos=('es_exito', 'sum')
        ).reset_index()

        # 4. Cálculos de Fallo
        diagnostico['rechazos'] = diagnostico['total_trans'] - diagnostico['exitos']
        diagnostico['pct_fallo'] = (diagnostico['rechazos'] / diagnostico['total_trans']) * 100
        
        return diagnostico

    def imprimir_reporte_segmentado(self, df_diag):
        print("\n" + "█"*115)
        print(f"{'DIAGNÓSTICO DE CALIDAD TÉCNICA POR FLUJO (PORT-IN vs PORT-OUT)':^115}")
        print("█"*115)
        header = f"{'MES':<10} | {'FLUJO':<12} | {'TOTAL TRANS.':<15} | {'ÉXITOS (200)':<15} | {'RECHAZOS':<12} | {'% FALLO'}"
        print(header)
        print("-" * 115)
        
        # Ordenar por mes para la lectura
        df_diag = df_diag.sort_values(['mes', 'flujo'], ascending=[True, False])

        for _, r in df_diag.iterrows():
            # Resaltar si el fallo es alto (>10%)
            alerta = "⚠️" if r['pct_fallo'] > 10 else " "
            print(f"{r['mes']:<10} | {r['flujo']:<12} | {r['total_trans']:<15,.0f} | {r['exitos']:<15,.0f} | "
                  f"{r['rechazos']:<12,.0f} | {r['pct_fallo']:>6.2f}% {alerta}")
        
        print("-" * 115)
        print("💡 NOTA: PORT-IN incluye ACTIVACIÓN y EJECUCIÓN C. PORT-OUT corresponde a solicitudes de salida.")
        print("█"*115 + "\n")