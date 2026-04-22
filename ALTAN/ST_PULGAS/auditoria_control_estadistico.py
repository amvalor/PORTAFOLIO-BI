import pandas as pd
import numpy as np

class AuditoriaControlEstadistico:
    """
    Módulo de auditoría para validar la estabilidad de los procesos de 
    portabilidad mediante control estadístico de variabilidad y detección de outliers.
    """
    def __init__(self, df_limpio):
        # Necesitamos el DataFrame que contiene los tiempos de ejecución calculados
        if df_limpio is None or df_limpio.empty:
            raise ValueError("No hay datos para realizar la auditoría estadística.")
        
        # Filtramos para trabajar solo con los casos que tienen tracking de tiempo
        # (Es decir, que tienen tanto activación como éxito)
        self.df = df_limpio.dropna(subset=['duracion_hrs']).copy()

    def ejecutar_auditoria(self):
        """Calcula métricas de control para confirmar la salud del proceso."""
        
        # 1. Medidas de Localización Avanzada (Percentiles)
        # Nos dicen en qué tiempo se resuelve el "X%" de los casos.
        resumen_stats = self.df.groupby('mes_analisis').agg(
            media_hrs=('duracion_hrs', 'mean'),
            std_dev=('duracion_hrs', 'std'),
            p50_mediana=('duracion_hrs', 'median'),
            p90=('duracion_hrs', lambda x: x.quantile(0.90)),
            p95=('duracion_hrs', lambda x: x.quantile(0.95)),
            casos_totales=('msisdn_ported', 'count')
        ).reset_index()

        # 2. Coeficiente de Variación (CV) - Medida de Estabilidad
        # CV = (Desviación Estándar / Media) * 100
        resumen_stats['cv_pct'] = (resumen_stats['std_dev'] / resumen_stats['media_hrs']) * 100

        # Clasificación de la estabilidad según el CV
        # < 25%: Proceso Robusto | 25-50%: Inestabilidad Moderada | > 50%: Inestabilidad Crítica
        condiciones = [
            (resumen_stats['cv_pct'] <= 25),
            (resumen_stats['cv_pct'] > 25) & (resumen_stats['cv_pct'] <= 50),
            (resumen_stats['cv_pct'] > 50)
        ]
        etiquetas = ['ROBUSTO', 'INESTABLE', 'CRÍTICO']
        resumen_stats['diagnostico_estabilidad'] = np.select(condiciones, etiquetas, default='INDETERMINADO')

        return resumen_stats

    def identificar_outliers_iqr(self):
        """
        Detecta casos atípicos usando el Rango Intercuartílico (IQR).
        Desmiente si el SLA es bajo por culpa de pocos casos muy tardíos.
        """
        outliers_por_mes = []
        
        for mes in self.df['mes_analisis'].unique():
            df_mes = self.df[self.df['mes_analisis'] == mes]
            q1 = df_mes['duracion_hrs'].quantile(0.25)
            q3 = df_mes['duracion_hrs'].quantile(0.75)
            iqr = q3 - q1
            umbral_superior = q3 + (1.5 * iqr)
            
            casos_outliers = df_mes[df_mes['duracion_hrs'] > umbral_superior]
            
            outliers_por_mes.append({
                'mes': mes,
                'umbral_hrs': umbral_superior,
                'cantidad_outliers': len(casos_outliers),
                'pct_impacto': (len(casos_outliers) / len(df_mes)) * 100
            })
            
        return pd.DataFrame(outliers_por_mes)

    def imprimir_reporte_auditoria(self, df_stats, df_outliers):
        print("\n" + "═"*135)
        print(f"{'AUDITORÍA DE CONTROL ESTADÍSTICO Y ESTABILIDAD DEL PROCESO':^135}")
        print("═"*135)
        
        header = (f"{'MES':<10} | {'MEDIA HRS':<10} | {'CV %':<10} | {'P50':<8} | {'P90':<8} | "
                  f"{'P95':<8} | {'ESTADO':<12} | {'OUTLIERS':<10} | {'UMBRAL OUT.'}")
        print(header)
        print("-" * 135)

        # Unimos para imprimir en una sola línea
        df_merged = pd.merge(df_stats, df_outliers, left_on='mes_analisis', right_on='mes')

        for _, r in df_merged.iterrows():
            # Formatear el estado con un prefijo visual
            estado_visual = f"✅ {r['diagnostico_estabilidad']}" if r['diagnostico_estabilidad'] == 'ROBUSTO' else \
                           f"⚠️ {r['diagnostico_estabilidad']}" if r['diagnostico_estabilidad'] == 'INESTABLE' else \
                           f"🚨 {r['diagnostico_estabilidad']}"

            print(f"{r['mes_analisis']:<10} | "
                  f"{r['media_hrs']:>10.2f} | "
                  f"{r['cv_pct']:>9.1f}% | "
                  f"{r['p50_mediana']:>8.1f} | "
                  f"{r['p90']:>8.1f} | "
                  f"{r['p95']:>8.1f} | "
                  f"{estado_visual:<12} | "
                  f"{r['cantidad_outliers']:>10.0f} | "
                  f"{r['umbral_hrs']:>10.1f} hrs")

        print("-" * 135)
        print("GLOSARIO DE AUDITORÍA:")
        print("1. CV % (Coeficiente de Variación): Mide la fiabilidad de la media. >50% indica que el promedio NO es representativo.")
        print("2. P90/P95: Tiempo máximo en el que se resuelve el 90% y 95% de los casos respectivamente.")
        print("3. UMBRAL OUT.: Tiempo a partir del cual un caso se considera un error atípico del sistema (Outlier).")
        print("═"*135 + "\n")