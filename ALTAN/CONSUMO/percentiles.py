import pandas as pd
import numpy as np
import os

def calcular_percentiles_equitativos():
    ruta_archivo = r"C:\Users\▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀\▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀\BI\py\GENERAL\CONSUMOS\▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"
    
    if not os.path.exists(ruta_archivo):
        print(f"❌ Error: No se encuentra el archivo en {ruta_archivo}")
        return

    try:
        # 1. Carga y limpieza inicial
        df = pd.read_csv(ruta_archivo, engine='python')
        df.columns = [col.strip().upper() for col in df.columns]
        
        # Filtro de seguridad: solo registros con consumo y usuarios
        df = df[(df['CONSUMO_MB'] > 0) & (df['USUARIOS'] > 0)].copy()
        
        # 2. ORDENAR por consumo (Crucial para percentiles de valor)
        df = df.sort_values(by='CONSUMO_MB').reset_index(drop=True)
        
        # 3. CÁLCULO DE PESOS ACUMULADOS
        total_usuarios = df['USUARIOS'].sum()
        df['USUARIOS_ACUM'] = df['USUARIOS'].cumsum()
        
        # Calculamos el porcentaje de la población que representa cada fila acumulada
        df['PORCENTAJE_ACUM'] = (df['USUARIOS_ACUM'] / total_usuarios) * 100
        
        # 4. ASIGNACIÓN DE PERCENTIL (1 al 100)
        # Usamos np.clip para asegurar que el rango sea exactamente 1-100
        df['P'] = np.ceil(df['PORCENTAJE_ACUM']).astype(int)
        df['P'] = np.clip(df['P'], 1, 100)

        # 5. AGREGACIÓN FINAL POR PERCENTIL DE POBLACIÓN
        resumen = df.groupby('P').agg(
            N_USUARIOS=('USUARIOS', 'sum'),
            TOTAL_MB=('CONSUMO_MB', 'sum'),
            PROM_MB_OFERTA=('CONSUMO_MB', 'mean'),
            MIN_MB=('CONSUMO_MB', 'min'),
            MAX_MB=('CONSUMO_MB', 'max')
        ).reset_index()

        # 6. IMPRESIÓN PARA EXCEL
        print("\n" + "="*95)
        print(f"{'MATRIZ DE PERCENTILES POR POBLACIÓN (1% DE USUARIOS POR FILA)':^95}")
        print("="*95)
        print("P\tUSUARIOS\tTOTAL_MB\tPROM_MB_OFERTA\tMIN_MB\tMAX_MB")
        
        for _, row in resumen.iterrows():
            print(f"{int(row['P'])}\t{int(row['N_USUARIOS'])}\t{row['TOTAL_MB']:.2f}\t{row['PROM_MB_OFERTA']:.2f}\t{row['MIN_MB']:.2f}\t{row['MAX_MB']:.2f}")

        print("-" * 95)
        print(f"Total Usuarios Analizados: {total_usuarios:,}")
        print(f"Promedio de Usuarios por Percentil: {total_usuarios/100:,.2f}")
        print("="*95 + "\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    calcular_percentiles_equitativos()
