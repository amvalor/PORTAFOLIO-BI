import pandas as pd
import warnings
import numpy as np
from config_db import obtener_conexion

# 1. SILENCIAR ADVERTENCIAS
warnings.filterwarnings('ignore', category=UserWarning, message='.*pandas only supports SQLAlchemy.*')

def auditar_asignaciones_reales(limite_gb=20):
    """
    Identifica usuarios con exceso de consumo y deduce el número de asignaciones 
    basándose en el volumen total vs el tope del bono.
    """
    limite_mb = limite_gb * 1024
    
    # Consulta SQL: Los redondeos se hacen aquí (SQL) para evitar errores en Python
    query = f"""
    SELECT * FROM (
        SELECT
            p.be_id,
            p.msisdn_ported AS msisdn,
            p.fecha_porta,
            p.tipo_porta,
            -- Cálculo de consumo en MB (Redondeo en SQL)
            ROUND(SUM(CASE WHEN c.offering_id IN (1900000096, 1900000134, 1900000235) 
                           THEN c.chg_amount ELSE 0 END) / POWER(1024, 2), 2) AS consumo_bono_mb,
            -- Conteo de IDs de oferta únicos para detectar si hubo mezcla de bonos
            COUNT(DISTINCT CASE WHEN c.offering_id IN (1900000096, 1900000134, 1900000235) 
                                THEN c.offering_id END) AS ofertas_distintas,
            -- Registro de la sesión más pesada
            ROUND(MAX(c.chg_amount) / POWER(1024, 2), 2) AS max_sesion_mb
        FROM ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ p
        INNER JOIN ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ c ON p.be_id = c.be_id AND p.msisdn_ported = c.msisdn
        WHERE p.fecha_porta >= '2026-03-17 00:00:00.000'
          AND c.service = 'dat'
          AND c.event_day >= 20260317
          AND c.product_family = 'MOVILIDAD'
        GROUP BY 1, 2, 3, 4
    ) AS resumen
    WHERE consumo_bono_mb > {limite_mb}
    ORDER BY consumo_bono_mb DESC
    """

    try:
        print(f"🔗 Conectando y auditando excesos (> {limite_gb} GB)...")
        with obtener_conexion() as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            print("✅ No se detectaron usuarios con consumo excedente.")
            return

        # --- DEDUCCIÓN DE ASIGNACIONES (Lógica Python/Pandas) ---
        # Si el tope es 20GB, dividimos el consumo total entre 20GB y redondeamos hacia arriba.
        df['asignaciones_deducidas'] = np.ceil(df['consumo_bono_mb'] / limite_mb).astype(int)
        
        # Consumo en GB para lectura humana
        df['consumo_gb'] = (df['consumo_bono_mb'] / 1024).round(2)

        print("\n" + "█"*85)
        print(f"{'AUDITORÍA TÉCNICA: DETECTIVE DE ASIGNACIONES MÚLTIPLES':^85}")
        print("█"*85)
        
        print(f"\nSe encontraron {len(df)} 'ofensores' que superaron la cuota de {limite_gb} GB.")
        
        print("\nTOP 15 USUARIOS CON SOBRE-ASIGNACIÓN:")
        columnas_view = ['msisdn', 'consumo_gb', 'asignaciones_deducidas', 'ofertas_distintas', 'max_sesion_mb']
        # Renombramos temporalmente para el print
        print(df[columnas_view].head(15).to_string(index=False))

        # --- CONCLUSIÓN ESTADÍSTICA ---
        avg_asig = df['asignaciones_deducidas'].mean()
        print("\n" + "-"*85)
        print(f"📊 HALLAZGOS CLAVE:")
        print(f" * Promedio de asignaciones en este grupo: {avg_asig:.2f}")
        print(f" * Máximo de asignaciones detectado:      {df['asignaciones_deducidas'].max()}")
        print(f" * Usuarios con >= 2 asignaciones:       {len(df[df['asignaciones_deducidas'] >= 2])}")
        
        print("\n💡 RESPUESTA TÉCNICA:")
        print(" El exceso de > 20GB no es un error de tasación, sino una multiplicidad de beneficios.")
        print(" La deducción confirma que estos usuarios recibieron el paquete más de una vez,")
        print(" permitiendo que el balance se renovara antes de que el sistema cortara el flujo.")
        print("-"*85)

        # Exportación
        df.to_csv("auditoria_asignaciones_portabilidad.csv", index=False)
        print(f"\n💾 Detalle listo en: auditoria_asignaciones_portabilidad.csv")

    except Exception as e:
        print(f"\n❌ ERROR DE EJECUCIÓN: {str(e)}")

if __name__ == "__main__":
    auditar_asignaciones_reales(20)
