import pandas as pd
import warnings
import sys
import numpy as np
from config_db import obtener_conexion

# 1. SILENCIAR ADVERTENCIAS
warnings.filterwarnings('ignore', category=UserWarning, message='.*pandas only supports SQLAlchemy.*')

def generar_reporte():
    """
    Reporte de Portabilidades y Eficiencia de Bonos.
    Incluye: Máximo consumo y doble segmentación por Bins de 5GB.
    """
    
    # 2. CONSULTA SQL (Corregida)
    query = """
    WITH porta AS (
        SELECT 
            be_id, 
            msisdn_ported, 
            fecha_porta, 
            tipo_porta 
        FROM ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
        WHERE fecha_porta >= '2026-03-17 00:00:00.000'
    ),
    consumo_consolidado AS (
        SELECT
            be_id,
            msisdn,
            SUM(chg_amount) / POWER(1024, 2) AS total_consumo_mb,
            SUM(CASE WHEN offering_id = 1900000096 THEN chg_amount ELSE 0 END) / POWER(1024, 2) AS bono_096,
            SUM(CASE WHEN offering_id = 1900000134 THEN chg_amount ELSE 0 END) / POWER(1024, 2) AS bono_134,
            SUM(CASE WHEN offering_id = 1900000235 THEN chg_amount ELSE 0 END) / POWER(1024, 2) AS bono_235,
            MAX(CASE WHEN offering_id IN (1900000096, 1900000134, 1900000235) THEN 'Y' ELSE 'N' END) AS bono_promo
        FROM ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
        WHERE service = 'dat'
          AND event_day >= 20260317
          AND product_family = 'MOVILIDAD'
        GROUP BY 1, 2
    )
    SELECT
        porta.be_id,
        porta.msisdn_ported,
        porta.fecha_porta,
        porta.tipo_porta,
        COALESCE(consumo_consolidado.bono_promo, 'N') AS bono_promo,
        ROUND(COALESCE(consumo_consolidado.total_consumo_mb, 0), 2) AS total_consumo,
        ROUND(COALESCE(consumo_consolidado.bono_096, 0), 2) AS consumo_096,
        ROUND(COALESCE(consumo_consolidado.bono_134, 0), 2) AS consumo_134,
        ROUND(COALESCE(consumo_consolidado.bono_235, 0), 2) AS consumo_235
    FROM porta
    LEFT JOIN consumo_consolidado ON porta.be_id = consumo_consolidado.be_id AND porta.msisdn_ported = consumo_consolidado.msisdn
    """

    try:
        print("🔗 Conectando a la base de datos...")
        with obtener_conexion() as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            print("⚠️ No se encontraron datos para el periodo.")
            return

        # --- 3. PROCESAMIENTO ---
        total_portas = df['msisdn_ported'].nunique()
        df_con_bono = df[df['bono_promo'] == 'Y'].copy()
        total_con_bono = df_con_bono['msisdn_ported'].nunique()
        
        # Consumo específico de bonos
        df_con_bono['consumo_solo_bonos'] = df_con_bono['consumo_096'] + df_con_bono['consumo_134'] + df_con_bono['consumo_235']
        
        # Máximo consumo del segmento con bono
        max_consumo_bono = df_con_bono['consumo_solo_bonos'].max() if not df_con_bono.empty else 0
        
        # Filtro de Usuarios Activos (Con consumo > 0)
        df_activos = df_con_bono[df_con_bono['consumo_solo_bonos'] > 0].copy()
        total_activos = df_activos['msisdn_ported'].nunique()

        # Configuración de Bins de 5GB
        bins = [0, 5120, 10240, 15360, 20480, float('inf')]
        labels = ['0-5 GB', '5-10 GB', '10-15 GB', '15-20 GB', '>20 GB']

        # A. Distribución Universo Asignado
        df_con_bono['rango'] = pd.cut(df_con_bono['consumo_solo_bonos'], bins=bins, labels=labels, include_lowest=True)
        dist_asignados = df_con_bono.groupby('rango', observed=False).agg(u=('msisdn_ported', 'nunique'))
        dist_asignados['pct'] = (dist_asignados['u'] / total_con_bono * 100) if total_con_bono > 0 else 0

        # B. Distribución Solo Usuarios Activos
        df_activos['rango'] = pd.cut(df_activos['consumo_solo_bonos'], bins=bins, labels=labels, include_lowest=True)
        dist_activos = df_activos.groupby('rango', observed=False).agg(u=('msisdn_ported', 'nunique'))
        dist_activos['pct'] = (dist_activos['u'] / total_activos * 100) if total_activos > 0 else 0

        # --- 4. IMPRESIÓN ---
        print("\n" + "█"*75)
        print(f"{'REPORTE CONSUMO - BONO PORTA':^75}")
        print("█"*75)
        
        print(f"\n[1] VOLUMEN Y PENETRACIÓN")
        print(f"    - Total Portabilidades:        {total_portas:,}")
        print(f"    - Usuarios con Bono:           {total_con_bono:,} ({ (total_con_bono/total_portas*100):.1f}%)")
        print(f"    - Usuarios Activos (Uso >0):   {total_activos:,} ({ (total_activos/total_con_bono*100):.1f}% de los asignados)")

        print(f"\n[2] EFICIENCIA DE USO")
        print(f"    - MÁXIMO CONSUMO REGISTRADO:   {max_consumo_bono:,.2f} MB")
        print(f"    - Consumo Promedio (Activos):  {df_activos['consumo_solo_bonos'].mean():,.2f} MB")
        print(f"    - Share of Wallet (Bonos):     {(df_activos['consumo_solo_bonos'].sum() / df['total_consumo'].sum() * 100):.2f}%")

        print(f"\n[3] DISTRIBUCIÓN: UNIVERSO TOTAL ASIGNADO")
        print(f"    {'Rango':<12} | {'Usuarios':<10} | {'% Relativo':<12}")
        print(f"    {'-'*40}")
        for r, row in dist_asignados.iterrows():
            print(f"    {r:<12} | {row['u']:>10,.0f} | {row['pct']:>11.1f}%")

        print(f"\n[4] DISTRIBUCIÓN: SOLO USUARIOS ACTIVOS (CON CONSUMO)")
        print(f"    {'Rango':<12} | {'Usuarios':<10} | {'% Relativo':<12} | {'Visual'}")
        print(f"    {'-'*65}")
        for r, row in dist_activos.iterrows():
            barra = "■" * int(row['pct'] / 5)
            print(f"    {r:<12} | {row['u']:>10,.0f} | {row['pct']:>11.1f}% | {barra}")

        print(f"\n[5] DESGLOSE TRÁFICO POR OFERTA")
        print(f"    - Bono 096: {df['consumo_096'].sum():>15,.2f} MB")
        print(f"    - Bono 134: {df['consumo_134'].sum():>15,.2f} MB")
        print(f"    - Bono 235: {df['consumo_235'].sum():>15,.2f} MB")
        print("\n" + "█"*75)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    generar_reporte()
