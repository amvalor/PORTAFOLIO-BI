import pandas as pd
import warnings

# Silenciar avisos de versiones para una salida limpia
warnings.simplefilter(action='ignore', category=FutureWarning)

def generar_analisis_consolidado(path_csv):
    try:
        # 1. CARGA DE DATOS ÚNICA
        print(f"Leyendo archivo: {path_csv}...")
        df = pd.read_csv(path_csv)
        
        # 2. PROCESAMIENTO BASE
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100']
        df['rango_percentil'] = pd.cut(df['lugar_percentil_global'], bins=bins, labels=labels, include_lowest=True)
        
        # Métricas Globales
        total_consumo_global = df['total_consumo'].sum()
        total_usuarios = df['total_usuarios_unicos'].sum()
        
        # Métricas de Afinidad
        df['ratio_afinidad'] = (df['total_consumo_x_oferta'] / df['total_consumo']) * 100

        # --- BLOQUE 1: RESUMEN EJECUTIVO ---
        resumen_valor = df.groupby('rango_percentil', observed=False).agg({
            'total_consumo': 'sum',
            'total_usuarios_unicos': 'sum'
        })
        resumen_valor['%_consumo'] = (resumen_valor['total_consumo'] / total_consumo_global) * 100

        top_ofertas_vol = df.groupby('oferta').agg({
            'total_usuarios_unicos': 'sum',
            'total_consumo_x_oferta': 'sum'
        }).nlargest(5, 'total_usuarios_unicos')

        print("\n" + "="*85)
        print("   PARTE 1: RESUMEN DE CONSUMO Y PERCENTILES MARZO 2026")
        print("="*85)
        
        print(f"\n[MÉTRICAS GENERALES]")
        print(f"Total Usuarios Únicos: {total_usuarios:,}")
        print(f"Consumo Total Global:  {total_consumo_global:,.2f} MB")
        
        print(f"\n[CONCENTRACIÓN DE CONSUMO POR PERCENTIL]")
        print("{:<15} | {:<15} | {:<10}".format("Rango Percentil", "Consumo (MB)", "% Tráfico"))
        print("-" * 50)
        for index, row in resumen_valor.sort_index(ascending=False).iterrows():
            print("{:<15} | {:<15,.2f} | {:<10.2f}%".format(index, row['total_consumo'], row['%_consumo']))

        print(f"\n[TOP 5 OFERTAS POR VOLUMEN DE USUARIOS]")
        print("{:<15} | {:<15} | {:<15}".format("Oferta ID", "Usuarios", "Consumo Oferta"))
        print("-" * 50)
        for index, row in top_ofertas_vol.iterrows():
            print("{:<15} | {:<15,} | {:<15,.2f} MB".format(index, row['total_usuarios_unicos'], row['total_consumo_x_oferta']))

        # --- BLOQUE 2: ANÁLISIS PROFUNDO ---
        analisis_ofertas = df.groupby('oferta').agg({
            'total_usuarios_unicos': 'sum',
            'total_consumo_x_oferta': 'sum',
            'total_consumo': 'sum',
            'ratio_afinidad': 'mean'
        })
        analisis_ofertas['consumo_avg_usuario'] = analisis_ofertas['total_consumo'] / analisis_ofertas['total_usuarios_unicos']

        print("\n\n" + "="*85)
        print("   PARTE 2: ANÁLISIS PROFUNDO (OFERTAS VS CONSUMO GLOBAL)")
        print("="*85)
        
        print(f"\n[1. TOP 10 OFERTAS POR VALOR DEL USUARIO (CONSUMO TOTAL)]")
        print("{:<15} | {:<12} | {:<18} | {:<15} | {:<12}".format(
            "Oferta ID", "Usuarios", "Consumo Oferta", "Consumo Global", "Avg MB/User"))
        print("-" * 85)
        
        top_valor = analisis_ofertas.nlargest(10, 'consumo_avg_usuario')
        for index, row in top_valor.iterrows():
            print("{:<15} | {:<12,} | {:<15,.2f} | {:<15,.2f} | {:<12,.2f}".format(
                index, row['total_usuarios_unicos'], row['total_consumo_x_oferta'], 
                row['total_consumo'], row['consumo_avg_usuario']))

        print(f"\n[2. ÍNDICE DE AFINIDAD (DEPENDENCIA)]")
        print("{:<15} | {:<20} | {:<20}".format("Oferta ID", "% Afinidad", "Tipo de Usuario"))
        print("-" * 65)
        
        top_volumen = analisis_ofertas.nlargest(8, 'total_usuarios_unicos')
        for index, row in top_volumen.iterrows():
            tipo = "Cautivo (Solo Oferta)" if row['ratio_afinidad'] > 80 else "Mixto (Navega más)"
            print("{:<15} | {:<20.2f}% | {:<20}".format(index, row['ratio_afinidad'], tipo))

        print(f"\n[3. MATRIZ DE SEGMENTACIÓN (RANGOS DE VALOR VS OFERTA)]")
        for rango in ['91-100', '51-60', '0-10']:
            segmento = df[df['rango_percentil'] == rango]
            top_seg = segmento.groupby('oferta')['total_usuarios_unicos'].sum().nlargest(3)
            print(f"Rango {rango}: ", end="")
            for off_id, cant in top_seg.items():
                print(f"[{off_id}: {cant:,} users] ", end="")
            print()

        # --- BLOQUE 3: CONCLUSIÓN ---
        top_10_pct = resumen_valor.loc['91-100', '%_consumo']
        best_off = analisis_ofertas['consumo_avg_usuario'].idxmax()

        print("\n" + "="*85)
        print("   CONCLUSIONES Y HALLAZGOS CLAVE")
        print("-" * 85)
        print(f"-> CONCENTRACIÓN: El top 10% (91-100) concentra el {top_10_pct:.2f}% del tráfico.")
        print(f"-> ARPU INDIRECTO: La oferta {best_off} atrae a los usuarios con mayor consumo global.")
        print(f"-> RIESGO: Ofertas con Afinidad > 90% indican usuarios sin bolsas de datos que fueron analizadas.")
        print("="*85 + "\n")

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo en la ruta: {path_csv}")
    except Exception as e:
        print(f"Error general en el proceso: {e}")

if __name__ == "__main__":
    # Ruta del archivo
    ruta_archivo = r"C:\Users\alfredo.martinez\Documents\BI\CONSUMOS_PROMO_percentil_MAR2026.csv"
    generar_analisis_consolidado(ruta_archivo)