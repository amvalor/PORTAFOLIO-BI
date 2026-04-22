import pandas as pd

class AnalizadorBuckets:
    def __init__(self, df_tiempos_detalle):
        self.df = df_tiempos_detalle.copy()

    def calcular_buckets(self):
        # Definimos los cortes lógicos (Buckets)
        bins = [0, 8, 24, float('inf')]
        labels = ['01. Fast Track (0-8h)', '02. Standard (8-24h)', '03. Out of SLA (>24h)']
        
        self.df['bucket_tiempo'] = pd.cut(self.df['duracion_hrs'], bins=bins, labels=labels)
        
        # Agrupamos por mes y bucket
        posibles_columnas = ['mes_analisis_exito', 'mes_analisis']
        col_mes = next((c for c in posibles_columnas if c in self.df.columns), 'MES')
        
        distribucion = self.df.groupby([col_mes, 'bucket_tiempo'], observed=False).size().unstack(fill_value=0)
        
        # Convertimos a porcentajes para que la historia sea comparable entre meses
        dist_pct = distribucion.div(distribucion.sum(axis=1), axis=0) * 100
        return dist_pct

    def imprimir_reporte_buckets(self, df_pct):
        print("\n" + "╔" + "═"*90 + "╗")
        print(f"║{'COMPOSICIÓN DEL TIEMPO DE RESPUESTA (HISTORIA POR RANGOS)':^90}║")
        print("╚" + "═"*90 + "╝")
        
        for mes, fila in df_pct.iterrows():
            print(f"\n📅 MES: {mes}")
            print(f"{'-'*40}")
            for rango, valor in fila.items():
                # Creamos una pequeña barra visual para "aterrizar" el dato
                barra = "█" * int(valor / 5)
                print(f"{rango:<22} | {valor:>6.1f}% {barra}")