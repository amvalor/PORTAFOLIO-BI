# PORTABILIDAD/main_portabilidad.py
import time
import sys
from actualizar_portin_maestro import ejecutar_pipeline_portin
from actualizar_portout_maestro import ejecutar_pipeline_portout

def consola_principal():
    print("====================================================")
    print("   CONSOLA DE ACTUALIZACIÓN DE PORTABILIDAD (v1.0)  ")
    print("====================================================")
    print(f"Inicio del proceso: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("----------------------------------------------------")
    
    inicio_total = time.time()

    try:
        # --- EJECUCIÓN DE PORT-IN ---
        print("\n🚀 [1/2] Iniciando Actualización de PORT-IN...")
        inicio_in = time.time()
        ejecutar_pipeline_portin()
        fin_in = time.time()
        print(f"✅ PORT-IN finalizado en {round((fin_in - inicio_in)/60, 2)} min.")

        print("-" * 40)

        # --- EJECUCIÓN DE PORT-OUT ---
        print("\n🚀 [2/2] Iniciando Actualización de PORT-OUT...")
        inicio_out = time.time()
        ejecutar_pipeline_portout()
        fin_out = time.time()
        print(f"✅ PORT-OUT finalizado en {round((fin_out - inicio_out)/60, 2)} min.")

        tiempo_total = round((time.time() - inicio_total) / 60, 2)
        print("\n====================================================")
        print(f"✨ ¡PROCESO TOTAL EXITOSO! Tiempo total: {tiempo_total} min.")
        print(f"Fin del proceso: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("====================================================")

    except KeyboardInterrupt:
        print("\n\n🛑 Proceso cancelado manualmente por el usuario.")
        sys.exit()
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO EN LA CONSOLA: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    consola_principal()