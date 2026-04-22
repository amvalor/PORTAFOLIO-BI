🏥 Medical Census Data Extractor (ETL Pipeline)
Este proyecto forma parte de mi portafolio profesional de Business Intelligence. Consiste en un motor de extracción de datos desarrollado en Python para procesar censos hospitalarios complejos almacenados en formatos no estructurados (Microsoft Word).

📌 Objetivo del ProyectoAutomatizar la transición de registros médicos manuales (bitácoras diarias) hacia una base de datos consolidada de pacientes únicos. El script analiza múltiples archivos .docx, identifica patrones mediante expresiones regulares (RegEx) y genera una estructura de datos lista para análisis en Power BI o SQL.

🛠️ Stack Tecnológico
  - Lenguaje: Python 3.x
  - Librerías Clave:
      - pandas: Para la estructuración, limpieza y consolidación de datos.
      - python-docx: Para la minería de texto dentro de documentos Word (tablas y párrafos).
      - re (RegEx): Para la extracción de identificadores únicos (ECU), edades y fechas.
      
📋 Layout de Salida (Data Schema)
El script consolida la historia del paciente en una sola fila con los siguientes campos:
  Campo              Descripción
  TIPO DE ATENCION   Clasificación del servicio (ALGO, PALIA, HOSPITALIZADOS, etc.)
  ECU                Identificador único del paciente (Anonimizado para el portafolio)
  EDAD               Edad capturada dinámicamente desde el texto
  FECHA INICIO/FIN   Ciclo de vida de la atención dentro del periodo analizado
  DIAS DE ATENCION   Cálculo de estancia o recurrencia
  DIAGNOSTICO        Registro clínico más reciente
  TRATAMIENTO        Historial compilado de todas las notas médicas registradas
  MEDICAMENTO        Identificación de fármacos específicos mediante diccionarios
  FALLECE            Indicador booleano basado en minería de texto (NLP)

🚀 Desafíos Técnicos Resueltos
  - Parsing de Datos Mixtos: Capacidad de leer datos tanto de tablas formateadas como de texto plano dentro del mismo documento.
  - Limpieza de Caracteres Especiales: Implementación de filtros para eliminar saltos de línea y comas internas que suelen romper los archivos CSV/Excel.
  - Lógica de Consolidación: Algoritmo que agrupa múltiples entradas por ECU para determinar la primera y última fecha de atención sin importar el orden de los archivos.
  - Codificación Universal: Salida optimizada con utf-8-sig para garantizar la compatibilidad de caracteres latinos (ñ, tildes) en Microsoft Excel.

📖 Instrucciones de Uso
  - Colocar los archivos .docx en la carpeta configurada.
  - Ejecutar el script: python procesador_hospital.py.
  - El resultado se imprimirá en formato CSV en la consola, listo para ser procesado por el asistente de "Texto en columnas" de Excel.
  
Notas de Privacidad (Data Privacy)
  Nota: Este repositorio no contiene datos reales de pacientes. El script se proporciona como una prueba de concepto técnica. En entornos de producción, se recomienda la encriptación de campos PII (Personally Identifiable Information) antes de cualquier proceso de visualización.
