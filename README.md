# Mapas de lluvia multi modelo para El Salvador

Herramienta en Python para la generación de mapas de precipitación acumulada sobre El Salvador utilizando información de modelos numéricos de predicción meteorológica.

Actualmente el proyecto integra información de los modelos:

- GFS
- IFS/ECMWF

Los datos son obtenidos mediante [Herbie](https://herbie.readthedocs.io/) y procesados con herramientas de Python para generar acumulados de precipitación, combinar modelos y representar espacialmente los resultados.

## Objetivo

Desarrollar una herramienta reproducible para generar mapas de precipitación pronosticada que puedan utilizarse como apoyo para el análisis meteorológico y la toma de decisiones.

El proyecto está orientado inicialmente a la generación de acumulados de precipitación sobre El Salvador, utilizando una combinación ponderada de modelos numéricos.

## Metodología actual

Para cada modelo se obtiene el acumulado de precipitación correspondiente al período seleccionado.

La combinación de modelos se realiza mediante una ponderación definida por el usuario:

```text
P_final = peso_GFS × P_GFS + peso_IFS × P_IFS


Los pesos deben sumar 100 %.

Posteriormente, los datos se recortan espacialmente a la zona de interés y se generan los productos cartográficos correspondientes.

Productos

El proyecto permite generar:

Mapas de precipitación acumulada.
Límites departamentales de El Salvador.
Datos espaciales en formato GeoTIFF.
Visualizaciones cartográficas para períodos de precipitación seleccionados.
Estructura del proyecto
mapas-lluvia-multimodelo-el-salvador/
│
├── scripts/
│   ├── acumulado_gfs.py
│   ├── acumulado_ifs.py
│   └── combinar_modelos.py
│
├── shapefiles/
│   └── departamentos_el_salvador.geojson
│
├── mapas/
│   └── .gitkeep
│
├── .gitignore
├── environment.yml
└── README.md
Requisitos
Linux
Python 3.11
Conda
Acceso a Internet para la descarga de datos de los modelos

Las dependencias utilizadas por el entorno se encuentran en:

environment.yml
Instalación

Crear el entorno Conda:

conda env create -f environment.yml

Activar el entorno:

conda activate lluvia_es
Ejecución

El script principal es:

python scripts/combinar_modelos.py

El script permite seleccionar los parámetros necesarios para generar el acumulado y combinar los modelos disponibles en la versión actual del proyecto.

Datos meteorológicos

Los datos de los modelos numéricos se obtienen mediante Herbie.

Actualmente se utiliza:

GFS

Producto:

pgrb2.0p25

Variable de precipitación:

APCP
IFS / ECMWF

Producto:

oper

Variable:

tp
Área geográfica

El proyecto utiliza los límites administrativos de los 14 departamentos de El Salvador contenidos en:

shapefiles/departamentos_el_salvador.geojson

El archivo se encuentra en coordenadas geográficas WGS84 (EPSG:4326).

Estado del proyecto
Versión actual

Primera versión funcional.

Esta versión permite:

Descargar información de precipitación de GFS e IFS mediante Herbie.
Calcular precipitación acumulada para períodos seleccionados.
Normalizar las coordenadas espaciales.
Combinar los acumulados de GFS e IFS mediante pesos definidos por el usuario.
Representar la precipitación sobre El Salvador.
Utilizar los límites de los 14 departamentos.
Generar mapas cartográficos.
Exportar el resultado espacial en formato GeoTIFF.
Desarrollo futuro

Entre las líneas de desarrollo previstas se encuentran:

Incorporación de otros modelos disponibles mediante Herbie.
Automatización de la selección de modelos.
Evaluación de diferentes combinaciones y ponderaciones.
Mejoras en la representación cartográfica.
Incorporación de información topográfica.
Generación automatizada de productos meteorológicos.
Ampliación de los formatos de salida.
Nota

Este proyecto se encuentra en desarrollo. Las metodologías de combinación, selección de modelos y representación de la precipitación pueden modificarse conforme avance la evaluación técnica.

Autor

Amides Figueroa

El Salvador
