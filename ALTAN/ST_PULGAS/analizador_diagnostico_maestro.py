import pandas as pd
import numpy as np

class AnalizadorDiagnosticoMaestro:
    def __init__(self, df_raw, df_tiempos):
        self.df_raw = df_raw.copy()
        self.df_tiempos = df_tiempos.copy() if df_tiempos is not None else pd.DataFrame()
        
    def ejecutar_analisis_pareto_fallas(self):
        fallos = self.df_raw[self.df_raw['transaction_result'] != '200'].copy()
        if fallos.empty: return pd.DataFrame()

        pareto = fallos.groupby(['transaction_result', 'transaction_detail']).size().reset_index(name='conteo')
        pareto = pareto.sort_values(by='conteo', ascending=False)
        pareto['pct_individual'] = (pareto['conteo'] / pareto['conteo'].sum()) * 100
        pareto['pct_acumulado'] = pareto['pct_individual'].cumsum()
        return pareto

    def analizar_robustez_media(self):
        col_duracion = 'duracion_hrs'
        if col_duracion not in self.df_tiempos.columns:
            return "Datos de SLA no disponibles."

        # Limpieza de nulos para evitar la advertencia de auditoría
        df_stats_input = self.df_tiempos.dropna(subset=[col_duracion])
        if df_stats_input.empty: return "Sin muestras válidas."

        # Detectar el nombre de la columna de mes según el merge
        mes_col = 'mes_analisis_exito' if 'mes_analisis_exito' in df_stats_input.columns else 'mes_analisis'
        
        stats = df_stats_input.groupby(mes_col)[col_duracion].agg([
            ('promedio', 'mean'),
            ('mediana', 'median'),
            ('std_dev', 'std')
        ]).reset_index()
        
        # El sesgo indica si hay outliers (como procesos que tardaron semanas)
        stats['sesgo_pct'] = abs((stats['promedio'] - stats['mediana']) / (stats['mediana'] + 0.1)) * 100
        return stats

    def analizar_estacionalidad_carga(self):
        self.df_raw['load_processing_timestamp'] = pd.to_datetime(self.df_raw['load_processing_timestamp'])
        self.df_raw['hora'] = self.df_raw['load_processing_timestamp'].dt.hour
        carga = self.df_raw.groupby('hora').size().reset_index(name='volumen')
        carga['pct_carga'] = (carga['volumen'] / carga['volumen'].sum()) * 100
        return carga

    def imprimir_diagnostico_maestro(self, df_pareto, df_robustez, df_carga):
        print("\n╔" + "═"*113 + "╗")
        print(f"║{'DIAGNÓSTICO MAESTRO: PARETO, ROBUSTEZ Y ESTACIONALIDAD':^113}║")
        print("╚" + "═"*113 + "╝")

        # 1. Pareto
        print("\n[1] ANÁLISIS DE PARETO (TOP 5 FALLAS CRÍTICAS)")
        print("-" * 115)
        if isinstance(df_pareto, pd.DataFrame):
            print(f"{'CÓDIGO':<12} | {'DETALLE':<60} | {'VOL':<10} | {'% ACUM'}")
            for _, r in df_pareto.head(5).iterrows():
                marcador = "🚩" if r['pct_acumulado'] <= 80 else "  "
                print(f"{str(r['transaction_result']):<12} | {str(r['transaction_detail'])[:60]:<60} | {r['conteo']:<10,.0f} | {r['pct_acumulado']:>7.1f}% {marcador}")

        # 2. Robustez
        print("\n[2] VALIDACIÓN DE ROBUSTEZ (PROMEDIO vs MEDIANA)")
        print("-" * 115)
        if isinstance(df_robustez, pd.DataFrame):
            col_mes = df_robustez.columns[0]
            print(f"{'MES':<10} | {'PROMEDIO':<15} | {'MEDIANA':<15} | {'SESGO %':<12} | {'ESTADO'}")
            for _, r in df_robustez.iterrows():
                estado = "ESTABLE ✅" if r['sesgo_pct'] < 20 else "VOLÁTIL ⚠️"
                print(f"{r[col_mes]:<10} | {r['promedio']:>14.2f}h | {r['mediana']:>14.2f}h | {r['sesgo_pct']:>11.1f}% | {estado}")

        # 3. Carga
        print("\n[3] TOP 3 PICOS DE CARGA HORARIA")
        print("-" * 115)
        top_3 = df_carga.sort_values('volumen', ascending=False).head(3)
        for _, r in top_3.iterrows():
            print(f"Hora Pico: {int(r['hora']):02d}:00 hrs | Volumen: {r['volumen']:>10,.0f} transacciones | Concentración: {r['pct_carga']:.2f}%")