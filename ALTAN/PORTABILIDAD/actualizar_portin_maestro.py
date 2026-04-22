# PORTABILIDAD/actualizar_portin_maestro.py
import time
import warnings
from config_db import obtener_conexion

warnings.filterwarnings("ignore", category=UserWarning)

def ejecutar_pipeline_portin():
    conn = obtener_conexion()
    if not conn:
        print("🛑 Error de conexión con Impala.")
        return

    cursor = conn.cursor()
    
    # Queries de mantenimiento 
    sql_drop_temp = "DROP TABLE IF EXISTS analysis_aftersale.amv_portin_temp PURGE"
    sql_drop_main = "DROP TABLE IF EXISTS analysis_aftersale.amv_portin PURGE"
    
    # Paso 2: Respaldo de histórico
    sql_respaldo = """
    CREATE TABLE IF NOT EXISTS analysis_aftersale.amv_portin_temp
    AS
    SELECT 
    *
    FROM analysis_aftersale.amv_portin
    WHERE event_month BETWEEN (SELECT CAST(FROM_TIMESTAMP(NOW() - INTERVAL 13 MONTH, 'yyyyMM') AS INT)) AND (SELECT CAST(FROM_TIMESTAMP(NOW() - INTERVAL 3 MONTH, 'yyyyMM') AS INT))
    """

    # Paso 4: Query Maestra
    sql_principal = """
    CREATE TABLE IF NOT EXISTS analysis_aftersale.amv_portin
    AS
    WITH port AS (
        SELECT 
             be_id
            , CAST(load_processing_hour/10000 AS INT) AS event_month
            , load_processing_timestamp AS fecha_porta
            , operation
            , transaction_result
            , transaction_detail 
            , 520000000000 + msisdn_ported AS msisdn_ported
            , 520000000000 + msisdn_backup AS msisdn_backup
            , imsi
            , dida
            , rida 
            , dcr 
            , rcr
            , CASE 
                WHEN rcr = dcr THEN "INTRA ALTAN"
                ELSE "FUERA ALTAN"
            END AS tipo_porta
            , ROW_NUMBER () OVER (PARTITION BY msisdn_ported ORDER BY  load_processing_hour DESC) AS fila
        FROM bss.portability_logs
        WHERE CAST(load_processing_hour/10000 AS INT) >= (SELECT CAST(FROM_TIMESTAMP(NOW() - INTERVAL 2 MONTH, 'yyyyMM') AS INT))
        AND transaction_result = '200' 
        AND operation = 'Portabilidad IN C'
    )
    , cat_dida AS ( 
        SELECT 
            DISTINCT CAST(ido AS INT) AS id
            , short_name AS nombre_dida
        FROM catalog.catalog_operators_attachments_intx
    )
    , cat_rida AS ( 
        SELECT 
            CAST(id_participante AS INT) AS id
            , nombre_corto_participante AS nombre_rida
        FROM billing.catalog_port_operator
    )
    , cat_beid AS (
        SELECT 
            DISTINCT be_prod AS be_id
            , UPPER(cliente) AS client_name
            , marca_unica
        FROM analysis_reporting.sac_catalog_vf
        WHERE estado_general IN ('5. Integrado','6. Operando')
    )
    , oferta AS (
        SELECT 
            520000000000 + crm_subscriber.msisdn AS msisdn
            , crm_subscriber.imsi
            , crm_offers.offer_id
            , catalog_billing_product.rgu
            , catalog_billing_product.product_name 
            , catalog_billing_product.product_short_name
            , crm_offers.primary_flag
            , (crm_offers.exp_date - INTERVAL 6 HOUR) AS vigencia_oferta
            , catalog_billing_product.end_date
            , (crm_subscriber.active_date - INTERVAL 6 HOUR) AS active_date
            , IF (crm_subscriber.sub_state = "B01", NULL, (crm_subscriber.mod_date - INTERVAL 6 HOUR)) AS fecha_baja
            , IF (crm_subscriber.sub_state = "B01", DATEDIFF(NOW(),(crm_subscriber.active_date - INTERVAL 6 HOUR)),DATEDIFF((crm_subscriber.mod_date - INTERVAL 6 HOUR),(crm_subscriber.active_date - INTERVAL 6 HOUR))) AS dias_vivo
            , CASE 
                WHEN crm_subscriber.sub_state = "B01" THEN "ACTIVE"
                WHEN crm_subscriber.sub_state = "B02" THEN "DEACTIVE"
                WHEN crm_subscriber.sub_state = "B03" THEN "SUSPEND"
                WHEN crm_subscriber.sub_state = "B04" THEN "BARRING"
                WHEN crm_subscriber.sub_state = "B05" THEN "PENDING"
                WHEN crm_subscriber.sub_state = "B06" THEN "IDLE"
                WHEN crm_subscriber.sub_state = "B07" THEN "PREDEACTIVATED"
            END AS estatus 
            , crm_subscriber.be_id
        FROM bss.crm_subscriber
        LEFT JOIN bss.crm_offers ON crm_subscriber.be_id = crm_offers.be_id AND crm_subscriber.sub_id = crm_offers.sub_id 
        LEFT JOIN billing.catalog_billing_product ON catalog_billing_product.be_id = crm_subscriber.be_id AND crm_offers.offer_id = CAST (catalog_billing_product.offering_id AS INT) AND catalog_billing_product.end_date >= (crm_offers.exp_date - INTERVAL 6 HOUR) 
    )
    , distribuidor AS (
        SELECT 
            be_id 
            , imsi
            , msisdn_crm 
            , id_pos 
            , distribuidor 
        FROM service.usrs_wm_distribuidores 
    )
    , precio AS (
        SELECT 
            be_id
            , offering_id 
            , ROUND (tarifa_roam_bajo_prorrat, 2 ) AS tarifa_roam_bajo_prorrat 
        FROM analysis_bdl.catalogo_precios_mkt_hist_V1
        WHERE vigente = 'VIGENTE'
    )
    , ini AS (
        SELECT 
            port.be_id
            , port.event_month
            , port.fecha_porta
            , port.operation
            , port.transaction_result
            , port.transaction_detail 
            , port.msisdn_ported
            , port.msisdn_backup
            , port.imsi
            , oferta.offer_id
            , oferta.product_short_name
            , oferta.estatus
            , oferta.active_date
            , oferta.fecha_baja
            , oferta.dias_vivo
            , port.dida
            , port.rida
            , port.dcr
            , port.rcr
            , port.tipo_porta
            , cat_beid.client_name
            , distribuidor.id_pos
            , distribuidor.distribuidor
            , UPPER(TRIM(COALESCE(cat_dida.nombre_dida, cr_fallback.nombre_rida))) AS nombre_donante
            , COALESCE (precio.tarifa_roam_bajo_prorrat, 0) AS precio_mayorista
            , ROW_NUMBER () OVER (PARTITION BY port.imsi ORDER BY oferta.primary_flag DESC , port.fecha_porta DESC) AS fila_ini
        FROM port 
        LEFT JOIN cat_beid ON port.be_id = cat_beid.be_id
        LEFT JOIN cat_dida ON port.dida = cat_dida.id
        LEFT JOIN cat_rida ON port.rida = cat_rida.id
        LEFT JOIN cat_rida cr_fallback ON port.dida = cr_fallback.id
        LEFT JOIN oferta ON port.imsi = oferta.imsi AND port.be_id = oferta.be_id
        LEFT JOIN distribuidor ON port.imsi = distribuidor.imsi AND port.be_id = distribuidor.be_id
        LEFT JOIN precio ON oferta.offer_id = precio.offering_id
        WHERE port.fila = 1
    )
    SELECT 
        ini.be_id
        , ini.event_month
        , ini.msisdn_ported
        , ini.msisdn_backup
        , ini.imsi
        , ini.offer_id
        , ini.product_short_name
        , ini.estatus
        , ini.fecha_porta
        , ini.active_date
        , CAST(FROM_TIMESTAMP(ini.active_date, 'yyyyMM') AS INT) AS cosecha
        , DATEDIFF(ini.fecha_porta, ini.active_date) AS t_act_port
        , ROUND((UNIX_TIMESTAMP(ini.fecha_porta) - UNIX_TIMESTAMP(ini.active_date)) / 3600.0,0) AS horas_act_port
        , ini.fecha_baja
        , ini.dias_vivo
        , ini.operation
        , ini.tipo_porta
        , ini.client_name
        , ini.nombre_donante
        , ini.dcr
        , ini.id_pos
        , ini.distribuidor
        , IFNULL(
            IF(
                CAST(FROM_TIMESTAMP(ini.active_date, 'yyyyMM') AS INT) < 202501
                , 'ANTES DEL 2025'
                , CAST(FROM_TIMESTAMP(ini.active_date, 'yyyyMM') AS VARCHAR)
                )
            ,'SIN COSECHA'
            ) AS cosecha_grupo
        , ini.precio_mayorista
        , NOW () AS fecha_actualizacion_registro
    FROM ini
    WHERE fila_ini = 1
    """

    # Paso 5: Reintegración
    sql_insert_final = "INSERT INTO analysis_aftersale.amv_portin SELECT * FROM analysis_aftersale.amv_portin_temp"

    try:
        print("🚀 Iniciando Pipeline Port-IN...")
        
        print("🔹 Pasos 1 y 2: Creando respaldo temporal...")
        cursor.execute(sql_drop_temp)
        cursor.execute(sql_respaldo)
        
        print("🔹 Paso 3: Limpiando tabla principal...")
        cursor.execute(sql_drop_main)
        
        print("🔹 Paso 4: Procesando datos nuevos (Fase pesada)...")
        cursor.execute(sql_principal)
        
        print("🔹 Paso 5: Reintegrando histórico y limpiando...")
        cursor.execute(sql_insert_final)
        cursor.execute(sql_drop_temp)
        
        conn.commit()
        print("✨ ¡Actualización de tabla Port-IN completado con éxito!")

    except Exception as e:
        print(f"❌ Error en el proceso: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    ejecutar_pipeline_portin()