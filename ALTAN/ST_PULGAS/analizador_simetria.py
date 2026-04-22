import pandas as pd
import numpy as np

class AnalizadorSimetria:
    def __init__(self, df_tiempos_detalle):
        self.df = df_tiempos_detalle.copy() if df_tiempos_detalle is not None else pd.DataFrame()

    def calcular_metricas_estabilidad(self):
        if self.df.empty:
            return pd.DataFrame()

        # Buscamos dinámicamente la columna del mes (usualmente mes_analisis_exito)
        posibles_columnas = ['mes_analisis_exito', 'mes_analisis', 'mes_analisis_ex_final']
        col_mes = next((c for c in posibles_columnas if c in self.df.columns), None)

        if not col_mes:
            raise KeyError("No se encontró una columna de tiempo/mes válida en el detalle.")

        # Agrupamos y calculamos nuestra Métrica Reina: CV
        stats = self.df.groupby(col_mes)['duracion_hrs'].agg([
            ('promedio', 'mean'),
            ('desv_est', 'std'),
            ('mediana', 'median')
        ]).reset_index()

        # Cálculo del Coeficiente de Variación (CV = Desviación / Promedio)
        stats['cv'] = stats['desv_est'] / stats['promedio']
        
        # Renombramos la columna del mes para el reporte
        stats.rename(columns={col_mes: 'MES'}, inplace=True)
        
        return stats

    def imprimir_reporte_simetria(self, df_stats):
        if df_stats.empty:
            print("⚠️ No hay datos suficientes para el análisis de simetría.")
            return

        print("\n" + "╔" + "═"*90 + "╗")
        print(f"║{'ANÁLISIS DE SIMETRÍA Y ESTABILIDAD (MÉTRICA REINA: CV)':^90}║")
        print("╚" + "═"*90 + "╝")
        
        header = f"{'MES':<10} | {'PROM.':<10} | {'MEDIANA':<10} | {'CV (ESTABILIDAD)':<18} | {'ESTADO'}"
        print(header)
        print("-" * 92)
        
        for _, r in df_stats.iterrows():
            cv = r['cv']
            # Interpretación estadística del CV
            if cv < 0.5:
                perfil = "ALTAMENTE ESTABLE ✅"
            elif cv <= 1.0:
                perfil = "ESTABLE"
            else:
                perfil = "DISPERSO (REVISAR) ⚠️"
            
            print(f"{r['MES']:<10} | {r['promedio']:>8.2f}h | {r['mediana']:>8.2f}h | {cv:>15.2f}    | {perfil}")
        print("-" * 92)