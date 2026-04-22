import pandas as pd
import numpy as np

class ReporteMetricasPulgas:
    def __init__(self, df_limpio):
        if df_limpio is None or df_limpio.empty:
            raise ValueError("No hay datos para procesar.")
        self.df = df_limpio
        self.df_con_tiempos = None

    def generar_metricas_finales(self):
        # 1. Separación de universos
        activaciones = self.df[self.df['operation'] == 'ACTIVACION DE PORTABILIDAD'][
            ['msisdn_ported', 'mes_analisis', 'load_processing_timestamp']
        ]
        exitos_in = self.df[self.df['operation'] == 'PORTABILIDAD IN C'][
            ['msisdn_ported', 'mes_analisis', 'load_processing_timestamp']
        ]
        salidas_out = self.df[self.df['operation'] == 'PORTABILIDAD OUT C'][
            ['msisdn_ported', 'mes_analisis']
        ]

        # 2. Tracking de Tiempos (SLA)
        tracking = pd.merge(
            exitos_in, 
            activaciones, 
            on='msisdn_ported', 
            how='left', 
            suffixes=('_exito', '_act')
        )

        # Cálculo de duración en horas
        tracking['duracion_hrs'] = (
            tracking['load_processing_timestamp_exito'] - 
            tracking['load_processing_timestamp_act']
        ).dt.total_seconds() / 3600

        # Guardamos el detalle para el Analizador Maestro
        self.df_con_tiempos = tracking

        # 3. Resumen por Mes
        resumen_act = activaciones.groupby('mes_analisis').size().reset_index(name='activacion')
        resumen_in = exitos_in.groupby('mes_analisis').size().reset_index(name='port_in_c')
        resumen_out = salidas_out.groupby('mes_analisis').size().reset_index(name='port_out_c')

        # 4. Cálculo de Transiciones (Éxitos sin activación en el mismo periodo)
        exitos_nativos = tracking[tracking['duracion_hrs'].notnull()].groupby('mes_analisis_exito').size()
        
        # 5. Consolidación
        df_final = resumen_act.merge(resumen_in, on='mes_analisis', how='left')
        df_final = df_final.merge(resumen_out, on='mes_analisis', how='left')
        
        df_final['exitos_nativos'] = df_final['mes_analisis'].map(exitos_nativos).fillna(0)
        df_final['transiciones'] = df_final['port_in_c'] - df_final['exitos_nativos']
        
        # KPIs
        df_final['efectividad_pct'] = (df_final['exitos_nativos'] / df_final['activacion'].replace(0,1)) * 100
        df_final['neta'] = df_final['port_in_c'] - df_final['port_out_c']
        
        # SLA 24H
        sla_cumplimiento = tracking[tracking['duracion_hrs'] <= 24].groupby('mes_analisis_exito').size()
        df_final['sla_24h_pct'] = (df_final['mes_analisis'].map(sla_cumplimiento).fillna(0) / 
                                   df_final['exitos_nativos'].replace(0,1)) * 100
        
        avg_hrs = tracking.groupby('mes_analisis_exito')['duracion_hrs'].mean()
        df_final['avg_hrs'] = df_final['mes_analisis'].map(avg_hrs).fillna(0)

        return df_final

    def imprimir_dashboard(self, df):
        print("\n" + "█"*135)
        print(f"{'DASHBOARD OPERATIVO DE CIERRE (EFECTIVIDAD & SLA 24H)':^135}")
        print("█"*135)
        header = (f"{'MES':<10} | {'ACTIVACIÓN':<11} | {'PORT-IN C':<11} | {'PORT-OUT':<11} | "
                  f"{'EFECT. %':<10} | {'NETA':<8} | {'TRANS.':<8} | {'AVG HRS':<8} | {'SLA 24H %'}")
        print(header)
        print("-" * 135)
        for _, r in df.iterrows():
            print(f"{r['mes_analisis']:<10} | {r['activacion']:>11,.0f} | {r['port_in_c']:>11,.0f} | "
                  f"{r['port_out_c']:>11,.0f} | {r['efectividad_pct']:>9.2f}% | {r['neta']:>8,.0f} | "
                  f"{r['transiciones']:>8,.0f} | {r['avg_hrs']:>8.1f} | {r['sla_24h_pct']:>9.2f}%")
        print("█"*135)