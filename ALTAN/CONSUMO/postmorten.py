import pandas as pd
import numpy as np
import warnings
from config_db import obtener_conexion

warnings.filterwarnings('ignore')

def ejecutar_auditoria_final_descriptiva(limite_gb=20):
    """
    Auditoría Sistémica con Narrativa de Negocio.
    Cada indicador incluye una descripción para evitar dudas en niveles gerenciales.
    """
    limite_mb = limite_gb * 1024
    
    query = """
    SELECT
        CAST(p.msisdn_ported AS STRING) AS msisdn,
        c.rating_group_name,
        c.offering_id,
        c.product_name,
        HOUR(c.mon_cust_local_start_date) AS hora,
        CAST(c.chg_amount AS DOUBLE) / 1048576 AS consumo_mb,
        c.mon_cust_local_start_date AS fecha_evento,
        p.fecha_porta
    FROM ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ p
    INNER JOIN ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ c 
        ON CAST(p.msisdn_ported AS STRING) = CAST(c.msisdn AS STRING)
    WHERE p.fecha_porta >= '2026-03-17'
      AND c.event_day >= 20260317
      AND c.service = 'dat'
      AND c.offering_id IN (1900000096, 1900000134, 1900000235)
    """

    try:
        with obtener_conexion() as conn:
            df_raw = pd.read_sql(query, conn)

        # Identificación del Grupo Maestro (Los 125)
        df_user_totals = df_raw.groupby('msisdn')['consumo_mb'].sum().reset_index()
        df_user_totals['asignaciones'] = np.ceil(df_user_totals['consumo_mb'] / limite_mb)
        msisdn_125 = df_user_totals[df_user_totals['asignaciones'] >= 2]['msisdn'].unique()
        df_of = df_raw[df_raw['msisdn'].isin(msisdn_125)].copy()
        df_of['fecha_evento'] = pd.to_datetime(df_of['fecha_evento'])
        
        print("\n" + "═"*95)
        print(f"{'REPORTE EXPLICATIVO DE AUDITORÍA: COMPORTAMIENTO SISTÉMICO (125 USUARIOS)':^95}")
        print("═"*95)

        # --- 1. IMPACTO POR RATING GROUP ---
        print("\n[1] EROSIÓN POR PROTOCOLO (¿En qué gastan el exceso?):")
        print("Muestra qué tipo de tráfico (Streaming, Redes, Navegación) genera la mayor pérdida.")
        rg_impacto = df_of.groupby('rating_group_name').agg({'consumo_mb': 'sum'})
        rg_impacto['%_Fuga'] = (rg_impacto['consumo_mb'] / df_of['consumo_mb'].sum() * 100).round(2)
        print(rg_impacto.nlargest(3, 'consumo_mb').round(2).to_string())

        # --- 2. VULNERABILIDAD POR PRODUCTO ---
        print("\n[2] PRODUCTOS AFECTADOS (¿Qué oferta comercial está fallando?):")
        print("Identifica el nombre comercial del bono que permitió la sobre-asignación.")
        prod_impacto = df_of.groupby('product_name').agg({'msisdn': 'nunique', 'consumo_mb': 'sum'})
        print(prod_impacto.nlargest(3, 'msisdn').round(2).to_string())

        # --- 3. CONCENTRACIÓN HORARIA ---
        print("\n[3] VENTANA CRÍTICA (¿A qué hora ocurre la fuga?):")
        print("Define si el exceso es por uso humano (día) o procesos automáticos (madrugada).")
        df_of['franja'] = pd.cut(df_of['hora'], bins=[-1,6,12,18,24], labels=['Madrugada','Mañana','Tarde','Noche'])
        print(df_of.groupby('franja')['consumo_mb'].sum().round(2).to_string())

        # --- 4. PERSISTENCIA ---
        print("\n[4] PERSISTENCIA DE CONEXIÓN (Abuso de Sesión):")
        print("Promedio de horas distintas al día en que el usuario genera tráfico.")
        persistencia = df_of.groupby(['msisdn', df_of['fecha_evento'].dt.date])['hora'].nunique().mean()
        print(f" > Resultado: {persistencia:.2f} horas/día. (Valores >12 indican uso industrial o compartido).")

        # --- 5. VENTANA DE ACTIVACIÓN ---
        print("\n[5] VELOCIDAD DE REACCIÓN (Días desde Portabilidad):")
        print("Días que transcurren desde que el usuario se porta hasta que detectamos el exceso.")
        v_reaccion = df_of.groupby('msisdn')['dias_desde_porta'].min().mean() if 'dias_desde_porta' in df_of else 0
        print(f" > Resultado: {v_reaccion:.2f} días. (Día 0 indica fraude premeditado).")

        # --- 6. INTENSIDAD PROMEDIO ---
        print("\n[6] INTENSIDAD POR CDR (Falla de Corte OCS):")
        print("Tamaño promedio de cada ticket de datos. Si es alto, el sistema no corta el flujo a tiempo.")
        print(f" > Resultado: {df_of['consumo_mb'].mean():.2f} MB por transacción.")

        # --- 7. EVENTOS DE RÁFAGA ---
        print("\n[7] EVENTOS DE RÁFAGA (Consumo Masivo):")
        print("Cantidad de veces que una sola sesión superó los 100MB sin ser interrumpida.")
        print(f" > Resultado: {len(df_of[df_of['consumo_mb'] > 100])} eventos detectados.")

        # --- 8. ENTROPÍA DE BENEFICIOS (ZOOM SOLICITADO) ---
        print("\n[8] ENTROPÍA DE BENEFICIOS (Bucle de Asignación):")
        print("Analiza si el usuario rompió un solo tipo de bono o múltiples ofertas simultáneas.")
        entropia = df_of.groupby('msisdn')['offering_id'].nunique().value_counts().sort_index()
        for num_bonos, cant_users in entropia.items():
            desc = "Usuarios atrapados en un bucle de una SOLA oferta." if num_bonos == 1 else f"Usuarios que saltaron entre {num_bonos} ofertas distintas."
            print(f" > {num_bonos} Bono(s): {cant_users} usuarios. ({desc})")

        # --- 9. CONCENTRACIÓN PARETO ---
        print("\n[9] LEY DE PARETO (Concentración del Daño):")
        print("Porcentaje de la fuga total generado solo por los 5 usuarios más agresivos.")
        top_5 = df_of.groupby('msisdn')['consumo_mb'].sum().nlargest(5).sum()
        print(f" > Resultado: {((top_5/df_of['consumo_mb'].sum())*100):.2f}% del daño total.")

        # --- 10. VOLATILIDAD ---
        print("\n[10] COEFICIENTE DE VARIACIÓN (Estabilidad del Error):")
        print("Si es bajo, el error es constante en todos. Si es alto, hay casos aislados extremos.")
        cv = (df_of.groupby('msisdn')['consumo_mb'].sum().std() / df_of.groupby('msisdn')['consumo_mb'].sum().mean()) * 100
        print(f" > Resultado: {cv:.2f}%.")

        print("\n" + "═"*95)

    except Exception as e:
        print(f"❌ Error en la auditoría descriptiva: {str(e)}")

if __name__ == "__main__":
    ejecutar_auditoria_final_descriptiva()
