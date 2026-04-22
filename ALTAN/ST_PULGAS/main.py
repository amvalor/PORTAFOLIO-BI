import sys
import warnings
from extractor import ExtractorPulgas
from analizador_calidad import AnalizadorCalidadPulgas
from limpiador import LimpiadorPulgas
from reporte_general import ReporteGeneralPulgas
from reporte_metricas import ReporteMetricasPulgas
from analizador_diagnostico_maestro import AnalizadorDiagnosticoMaestro
from analizador_simetria import AnalizadorSimetria
from analizador_buckets import AnalizadorBuckets

# Configuración de limpieza de consola
warnings.filterwarnings("ignore", category=UserWarning)

def ejecutar_sistema_st_pulgas():
    """
    Orquestador del Proyecto St Pulgas con enfoque en Simetría Operativa (CV).
    """
    print("\n=== Iniciando Sistema de Análisis Modular - Proyecto St Pulgas ===\n")

    # EXTRACCIÓN
    extractor = ExtractorPulgas()
    df_raw = extractor.ejecutar_extraccion()
    
    if df_raw is None or df_raw.empty:
        print("❌ Error: No se obtuvieron datos.")
        sys.exit(1)

    # DIAGNÓSTICO DE CALIDAD TÉCNICA
    try:
        calidad = AnalizadorCalidadPulgas(df_raw)
        df_diagnostico = calidad.generar_diagnostico_segmentado()
        calidad.imprimir_reporte_segmentado(df_diagnostico)
    except Exception as e:
        print(f"⚠️ Nota en Calidad: {e}")

    # LIMPIEZA
    limpiador = LimpiadorPulgas(df_raw)
    df_clean = (limpiador
                .normalizar_formatos()
                .filtrar_exitos_reales()
                .depurar_nulos_criticos()
                .obtener_datos_limpios())

    # REPORTE GENERAL (Volúmenes)
    try:
        analizador_gral = ReporteGeneralPulgas(df_clean)
        resumen_gral = analizador_gral.obtener_totales_portabilidad()
        analizador_gral.imprimir_dashboard_consola(resumen_gral)
    except Exception as e:
        print(f"⚠️ Nota en Reporte General: {e}")

    # MÉTRICAS DE NEGOCIO Y SLA
    df_tiempos_detalle = None
    try:
        metricas = ReporteMetricasPulgas(df_clean)
        df_resumen_kpi = metricas.generar_metricas_finales()
        metricas.imprimir_dashboard(df_resumen_kpi)
        df_tiempos_detalle = metricas.df_con_tiempos 
    except Exception as e:
        print(f"❌ Error en Métricas: {e}")

    # DIAGNÓSTICO MAESTRO (Pareto y Robustez)
    try:
        maestro = AnalizadorDiagnosticoMaestro(df_raw, df_tiempos_detalle)
        df_p = maestro.ejecutar_analisis_pareto_fallas()
        df_r = maestro.analizar_robustez_media()
        df_c = maestro.analizar_estacionalidad_carga()
        maestro.imprimir_diagnostico_maestro(df_p, df_r, df_c)
    except Exception as e:
        print(f"⚠️ Nota en Diagnóstico Maestro: {e}")

    # ANÁLISIS DE SIMETRÍA 
    if df_tiempos_detalle is not None:
        try:
            simetria = AnalizadorSimetria(df_tiempos_detalle)
            df_estabilidad = simetria.calcular_metricas_estabilidad()
            simetria.imprimir_reporte_simetria(df_estabilidad)
        except Exception as e:
            print(f"⚠️ Nota en Análisis de Simetría: {e}")

    # COMPOSICIÓN POR BUCKETS (Zoom Suave)
    if df_tiempos_detalle is not None:
        try:
            buckets = AnalizadorBuckets(df_tiempos_detalle)
            df_dist_buckets = buckets.calcular_buckets()
            buckets.imprimir_reporte_buckets(df_dist_buckets)
        except Exception as e:
            print(f"⚠️ Nota en Análisis de Buckets: {e}")

    print("\n✅ Análisis estructural y operativo finalizado.")

if __name__ == "__main__":
    ejecutar_sistema_st_pulgas()