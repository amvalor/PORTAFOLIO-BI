📡 Auditoría de Red: Análisis y Comportamiento de Uso (ALTAN)
Este repositorio contiene la lógica de negocio y los scripts de optimización desarrollados para la auditoría y análisis de datos masivos en la infraestructura de Altan Redes. El enfoque principal es la detección de anomalías y la validación de integridad en los registros de consumo (CDRs) y portabilidades.

🔍 Contexto del Proyecto
En el sector de telecomunicaciones, la discrepancia entre el consumo de red y la facturación puede representar fugas de ingresos significativas. Este proyecto implementa un pipeline de análisis para auditar el comportamiento de los usuarios y garantizar que la data refleje la realidad operativa.

🛠️ Desafíos Técnicos y Soluciones
1. Optimización en Entornos Big Data (Impala/Cloudera)
Problema: Las consultas a tablas con millones de registros fallaban frecuentemente debido al error de protocolo Thrift (08S01) por saturación de red o tiempo de espera.
Solución: Implementación de lógicas de agregación por vigencia y segmentación de queries. Se optimizaron los joins y filtros para reducir el "payload" de la consulta, permitiendo extracciones estables y rápidas hacia Python para análisis posterior.

2. Análisis de Cohortes (Churn & Retention)
Metodología: Clasificación de usuarios por mes de activación para observar su ciclo de vida y patrones de consumo a lo largo del tiempo.
Impacto: Identificación de los periodos de mayor deserción y detección de grupos de usuarios con comportamientos de uso atípicos (Heavy Users vs. Ghost Users).

3. Auditoría Forense de Datos
Validación de Integridad: Cruce de bases de datos de consumo contra maestros de facturación para identificar anomalías en la tasación de servicios de voz y datos.
Estadística Descriptiva: Uso de la mediana y desviación estándar para identificar outliers, yendo más allá del promedio simple para entender la verdadera distribución del tráfico de red.

📊 Stack Tecnológico
SQL (Impala/Hadoop): Extracción y transformación de datos en el clúster.
Python (Pandas & NumPy): Procesamiento de datos, limpieza y cálculos estadísticos de cohortes.
DBeaver: Gestión y tunning de queries complejas.
Git: Control de versiones para asegurar la trazabilidad de las fórmulas de auditoría.
