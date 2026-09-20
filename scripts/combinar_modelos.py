from datetime import datetime
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import xarray as xr
from herbie import Herbie
from matplotlib.colors import LinearSegmentedColormap
from rasterio.transform import from_bounds
from scipy.interpolate import RegularGridInterpolator
from shapely import contains_xy

# ============================================================
# 1. DATOS DEL USUARIO
# ============================================================

fecha_corrida = input(
    "Fecha/hora de corrida de los modelos (YYYY-MM-DD HH:MM): "
)

fecha_inicio = input(
    "Fecha/hora inicial del acumulado (YYYY-MM-DD HH:MM): "
)

fecha_final = input(
    "Fecha/hora final del acumulado   (YYYY-MM-DD HH:MM): "
)

peso_gfs = float(
    input("Peso GFS (%): ")
)

peso_ifs = float(
    input("Peso IFS (%): ")
)


# ============================================================
# 2. CONVERTIR FECHAS
# ============================================================

corrida = datetime.strptime(
    fecha_corrida,
    "%Y-%m-%d %H:%M"
)

inicio = datetime.strptime(
    fecha_inicio,
    "%Y-%m-%d %H:%M"
)

final = datetime.strptime(
    fecha_final,
    "%Y-%m-%d %H:%M"
)


# ============================================================
# 3. VALIDACIONES
# ============================================================

if final <= inicio:
    raise ValueError(
        "La fecha final debe ser posterior a la fecha inicial."
    )

if inicio < corrida:
    raise ValueError(
        "El inicio del acumulado no puede ser anterior "
        "a la corrida del modelo."
    )

if peso_gfs < 0 or peso_ifs < 0:
    raise ValueError(
        "Los pesos no pueden ser negativos."
    )

suma_pesos = peso_gfs + peso_ifs

if abs(suma_pesos - 100) > 0.001:
    raise ValueError(
        f"Los pesos deben sumar 100 %. "
        f"Actualmente suman {suma_pesos:.2f} %."
    )


# ============================================================
# 4. CALCULAR FORECASTS
# ============================================================

horas_inicio = (
    inicio - corrida
).total_seconds() / 3600

horas_final = (
    final - corrida
).total_seconds() / 3600


if horas_inicio % 24 != 0:
    raise ValueError(
        "El inicio debe coincidir con un paso de 24 horas "
        "respecto a la corrida."
    )

if horas_final % 24 != 0:
    raise ValueError(
        "El final debe coincidir con un paso de 24 horas "
        "respecto a la corrida."
    )


f_inicio = int(horas_inicio)
f_final = int(horas_final)


# ============================================================
# 5. MOSTRAR CONFIGURACIÓN
# ============================================================

print("\n==========================================")
print("CONFIGURACIÓN")
print("==========================================")

print(f"Corrida           : {corrida}")
print(f"Inicio acumulado  : {inicio}")
print(f"Final acumulado   : {final}")

print(f"\nForecast inicial  : F{f_inicio:03d}")
print(f"Forecast final    : F{f_final:03d}")

print("\nPesos:")
print(f"  GFS : {peso_gfs:.1f} %")
print(f"  IFS : {peso_ifs:.1f} %")


# ============================================================
# 6. FUNCIÓN PARA LEER GFS
# ============================================================

def leer_gfs(forecast):

    dias = forecast // 24

    print(f"\nDescargando GFS F{forecast:03d}...")

    H = Herbie(
        corrida,
        model="gfs",
        product="pgrb2.0p25",
        fxx=forecast
    )

    ds = H.xarray(
        f":APCP:surface:0-{dias} day acc fcst:"
    )

    variable = list(ds.data_vars)[0]

    apcp = ds[variable]

    # GFS: kg/m² = mm de precipitación
    apcp_mm = apcp

    print(
        f"GFS F{forecast:03d}: "
        f"máximo = {float(apcp_mm.max()):.2f} mm"
    )

    return apcp_mm


# ============================================================
# 7. FUNCIÓN PARA LEER IFS
# ============================================================

def leer_ifs(forecast):

    print(f"\nDescargando IFS F{forecast:03d}...")

    H = Herbie(
        corrida,
        model="ifs",
        product="oper",
        fxx=forecast
    )

    ds = H.xarray(":tp:")

    tp = ds["tp"]

    # IFS: metros → milímetros
    tp_mm = tp * 1000

    print(
        f"IFS F{forecast:03d}: "
        f"máximo = {float(tp_mm.max()):.2f} mm"
    )

    return tp_mm


# ============================================================
# 8. CALCULAR ACUMULADO GFS
# ============================================================

print("\n==========================================")
print("CALCULANDO GFS")
print("==========================================")

if f_inicio == 0:

    print("El inicio coincide con la corrida.")

    gfs_inicio = 0

else:

    gfs_inicio = leer_gfs(f_inicio)


gfs_final = leer_gfs(f_final)


if f_inicio == 0:

    lluvia_gfs = gfs_final

else:

    lluvia_gfs = (
        gfs_final - gfs_inicio
    ).clip(min=0)


# ============================================================
# 9. CALCULAR ACUMULADO IFS
# ============================================================

print("\n==========================================")
print("CALCULANDO IFS")
print("==========================================")

if f_inicio == 0:

    print("El inicio coincide con la corrida.")

    ifs_inicio = 0

else:

    ifs_inicio = leer_ifs(f_inicio)


ifs_final = leer_ifs(f_final)


if f_inicio == 0:

    lluvia_ifs = ifs_final

else:

    lluvia_ifs = (
        ifs_final - ifs_inicio
    ).clip(min=0)


# ============================================================
# 10. COMPROBAR LAS GRILLAS
# ============================================================

print("\n==========================================")
print("COMPROBANDO GRILLAS")
print("==========================================")

print("GFS:")
print(f"  Dimensiones: {lluvia_gfs.dims}")
print(f"  Tamaño:      {lluvia_gfs.shape}")

print("\nIFS:")
print(f"  Dimensiones: {lluvia_ifs.dims}")
print(f"  Tamaño:      {lluvia_ifs.shape}")


# ============================================================
# 11. NORMALIZAR LONGITUDES
# ============================================================

def normalizar_longitud(data):

    data = data.assign_coords(
        longitude=(
            ((data.longitude + 180) % 360) - 180
        )
    )

    data = data.sortby("longitude")

    return data


lluvia_gfs = normalizar_longitud(lluvia_gfs)

lluvia_ifs = normalizar_longitud(lluvia_ifs)


# ============================================================
# 12. COMPROBAR COORDENADAS
# ============================================================

print("\n==========================================")
print("COORDENADAS DESPUÉS DE NORMALIZAR")
print("==========================================")

print(
    f"GFS longitud: "
    f"{float(lluvia_gfs.longitude.min()):.2f} "
    f"→ "
    f"{float(lluvia_gfs.longitude.max()):.2f}"
)

print(
    f"IFS longitud: "
    f"{float(lluvia_ifs.longitude.min()):.2f} "
    f"→ "
    f"{float(lluvia_ifs.longitude.max()):.2f}"
)


# ============================================================
# 13. ALINEAR LAS GRILLAS
# ============================================================

lluvia_gfs, lluvia_ifs = xr.align(
    lluvia_gfs,
    lluvia_ifs,
    join="inner"
)


print("\nDespués de alinear:")
print(f"  GFS: {lluvia_gfs.shape}")
print(f"  IFS: {lluvia_ifs.shape}")
print("\nLatitudes:")
print(
    f"GFS: {float(lluvia_gfs.latitude.min()):.2f} "
    f"→ {float(lluvia_gfs.latitude.max()):.2f}"
)

print(
    f"IFS: {float(lluvia_ifs.latitude.min()):.2f} "
    f"→ {float(lluvia_ifs.latitude.max()):.2f}"
)


# ============================================================
# 12. COMBINAR MODELOS
# ============================================================

print("\n==========================================")
print("COMBINANDO MODELOS")
print("==========================================")

peso_gfs_decimal = peso_gfs / 100
peso_ifs_decimal = peso_ifs / 100


lluvia_final = (
    peso_gfs_decimal * lluvia_gfs
    +
    peso_ifs_decimal * lluvia_ifs
)


# ============================================================
# 13. RESULTADOS
# ============================================================

print("\n==========================================")
print("RESULTADO FINAL")
print("==========================================")

print(
    f"Período: {inicio} → {final}"
)

print(
    f"\nGFS:"
)

print(
    f"  Máximo: "
    f"{float(lluvia_gfs.max()):.2f} mm"
)

print(
    f"  Promedio: "
    f"{float(lluvia_gfs.mean()):.2f} mm"
)

print(
    f"\nIFS:"
)

print(
    f"  Máximo: "
    f"{float(lluvia_ifs.max()):.2f} mm"
)

print(
    f"  Promedio: "
    f"{float(lluvia_ifs.mean()):.2f} mm"
)

print(
    f"\nCOMBINADO:"
)

print(
    f"  Máximo: "
    f"{float(lluvia_final.max()):.2f} mm"
)

print(
    f"  Promedio: "
    f"{float(lluvia_final.mean()):.2f} mm"
)

print("\n==========================================")
print("PROCESO TERMINADO")
print("==========================================")

# ============================================================
# 14. RECORTAR A EL SALVADOR
# ============================================================

import geopandas as gpd
import numpy as np
from shapely import contains_xy

print("\n==========================================")
print("RECORTANDO A EL SALVADOR")
print("==========================================")

# Leer límites departamentales
archivo_geojson = (
    "/home/amides/mapas_lluvia/shapefiles/"
    "departamentos_el_salvador.geojson"
)

departamentos = gpd.read_file(archivo_geojson)

print(f"Departamentos encontrados: {len(departamentos)}")
print(f"CRS: {departamentos.crs}")

# Unir los 14 departamentos
el_salvador = departamentos.geometry.union_all()

# Obtener límites de El Salvador
xmin, ymin, xmax, ymax = departamentos.total_bounds

# Margen de datos alrededor del territorio
margen_datos = 0.5

print("\nOrden de latitudes:")
print(f"Primera: {float(lluvia_final.latitude.values[0])}")
print(f"Última:  {float(lluvia_final.latitude.values[-1])}")

# Recortar la grilla usando los límites + margen
lluvia_el_salvador = lluvia_final.sel(
    longitude=slice(
        xmin - margen_datos,
        xmax + margen_datos
    ),
    latitude=slice(
        ymax + margen_datos,
        ymin - margen_datos
    )
)

print("\nResultado del recorte:")
print(f"Dimensiones: {lluvia_el_salvador.shape}")

print("\n==========================================")
print("RECORTE TERMINADO")
print("==========================================")

# ============================================================
# 15. COMPROBAR LÍMITES DEPARTAMENTALES
# ============================================================

import matplotlib.pyplot as plt

print("\n==========================================")
print("COMPROBANDO LÍMITES DEPARTAMENTALES")
print("==========================================")

# Crear figura
fig, ax = plt.subplots(figsize=(8, 8))

# Dibujar precipitación recortada
lluvia_el_salvador.plot(
    ax=ax,
    cmap="viridis",
    add_colorbar=True
)

# Dibujar límites departamentales
departamentos.boundary.plot(
    ax=ax,
    edgecolor="black",
    linewidth=1
)

# Margen visual adicional del mapa
margen_mapa = 0.02

ax.set_xlim(
    float(lluvia_el_salvador.longitude.min()) - margen_mapa,
    float(lluvia_el_salvador.longitude.max()) + margen_mapa
)

ax.set_ylim(
    float(lluvia_el_salvador.latitude.min()) - margen_mapa,
    float(lluvia_el_salvador.latitude.max()) + margen_mapa
)

ax.set_xlabel("Longitud")
ax.set_ylabel("Latitud")

plt.tight_layout()

# Guardar prueba
plt.savefig(
    "/home/amides/mapas_lluvia/mapas/prueba_departamentos.png",
    dpi=150
)

# ============================================================
# 15. MAPA METEOROLÓGICO
# ============================================================

from matplotlib.colors import LinearSegmentedColormap
from scipy.interpolate import RegularGridInterpolator


print("\n==========================================")
print("GENERANDO MAPA METEOROLÓGICO")
print("==========================================")


# ------------------------------------------------------------
# 1. COLORES AUTORIZADOS
# ------------------------------------------------------------

colores_autorizados = [
    "#c5c8cf",
    "#7898d8",
    "#286cff",
    "#0045ff",
    "#002b75",
    "#b7ee40",
    "#eee152",
    "#f57046",
]

cmap = LinearSegmentedColormap.from_list(
    "precipitacion_autorizada",
    colores_autorizados,
    N=256
)


# ------------------------------------------------------------
# 2. EXTRAER DATOS
# ------------------------------------------------------------

lon = lluvia_el_salvador.longitude.values
lat = lluvia_el_salvador.latitude.values

datos = lluvia_el_salvador.values


# ------------------------------------------------------------
# 3. INTERPOLACIÓN VISUAL
# ------------------------------------------------------------
#
# Esto NO modifica los datos originales.
# Solamente crea una grilla más fina para representar
# visualmente la precipitación de manera más suave.
#

numero_longitudes = 250
numero_latitudes = 180

lon_nuevo = np.linspace(
    lon.min(),
    lon.max(),
    numero_longitudes
)

lat_nuevo = np.linspace(
    lat.min(),
    lat.max(),
    numero_latitudes
)

lon_mesh, lat_mesh = np.meshgrid(
    lon_nuevo,
    lat_nuevo
)


# La latitud original está descendente.
# Para interpolar correctamente necesitamos invertirla.

lat_interpolacion = lat[::-1]
datos_interpolacion = datos[::-1, :]


interpolador = RegularGridInterpolator(
    (
        lat_interpolacion,
        lon
    ),
    datos_interpolacion,
    method="linear",
    bounds_error=False,
    fill_value=np.nan
)


puntos = np.column_stack(
    [
        lat_mesh.ravel(),
        lon_mesh.ravel()
    ]
)


datos_suavizados = interpolador(
    puntos
).reshape(
    lat_mesh.shape
)


# ------------------------------------------------------------
# 4. MÁSCARA VISUAL DE EL SALVADOR
# ------------------------------------------------------------
#
# IMPORTANTE:
# Esta máscara solamente afecta la visualización.
# NO modifica lluvia_el_salvador.
#

geometria_el_salvador = departamentos.geometry.union_all()

mascara_mapa = contains_xy(
    geometria_el_salvador,
    lon_mesh,
    lat_mesh
)

datos_mapa = np.where(
    mascara_mapa,
    datos_suavizados,
    np.nan
)


# ------------------------------------------------------------
# 5. CREAR FIGURA
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(11, 8)
)


# ------------------------------------------------------------
# 6. NIVELES DE PRECIPITACIÓN
# ------------------------------------------------------------

# Campo de precipitación suave entre 10 y 250 mm
niveles_suaves = np.linspace(
    10,
    250,
    256
)

# Isohietas cada 50 mm
niveles_etiquetas = np.arange(
    50,
    251,
    50
)

imagen = ax.contourf(
    lon_mesh,
    lat_mesh,
    datos_mapa,
    levels=niveles_suaves,
    cmap=cmap,
    extend="max"
)

# ------------------------------------------------------------
# ETIQUETAS DE PRECIPITACIÓN
# ------------------------------------------------------------

contornos_etiquetas = ax.contour(
    lon_mesh,
    lat_mesh,
    datos_mapa,
    levels=niveles_etiquetas,
    colors="#555555",
    linewidths=0.45,
    alpha=0.65,
    zorder=4
)

ax.clabel(
    contornos_etiquetas,
    levels=niveles_etiquetas,
    inline=True,
    inline_spacing=5,
    fmt=lambda x: f"{x:g}",
    fontsize=6,
    colors="#333333",
    rightside_up=True
)

# Hacer las etiquetas más visibles
for texto in ax.texts:
    texto.set_fontweight("bold")
    texto.set_color("#333333")


# ------------------------------------------------------------
# 7. LÍMITES DEPARTAMENTALES
# ------------------------------------------------------------

departamentos.boundary.plot(
    ax=ax,
    color="black",
    linewidth=0.8,
    zorder=5
)


# ------------------------------------------------------------
# 8. LÍMITE EXTERIOR DE EL SALVADOR
# ------------------------------------------------------------

gpd.GeoSeries(
    [geometria_el_salvador],
    crs=departamentos.crs
).boundary.plot(
    ax=ax,
    color="black",
    linewidth=1.5,
    zorder=6
)


# ------------------------------------------------------------
# 9. BARRA DE COLORES
# ------------------------------------------------------------

cbar = fig.colorbar(
    imagen,
    ax=ax,
    pad=0.02,
    shrink=0.88
)

cbar.set_label(
    "Precipitación Acumulada (mm)",
    fontsize=11
)

cbar.set_ticks(
    np.arange(50, 251, 50)
)


# ------------------------------------------------------------
# 10. TÍTULO
# ------------------------------------------------------------
meses = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]

fecha_inicio_texto = (
    f"{inicio.day} de "
    f"{meses[inicio.month - 1]} de "
    f"{inicio.year}"
)

fecha_final_texto = (
    f"{final.day} de "
    f"{meses[final.month - 1]} de "
    f"{final.year}"
)

ax.set_title(
    "Precipitación Pronosticada\n"
    f"{fecha_inicio_texto} al {fecha_final_texto}",
    fontsize=16,
    fontweight="bold",
    pad=12
)


# ------------------------------------------------------------
# 11. EXTENSIÓN DEL MAPA
# ------------------------------------------------------------

# El mapa se ajusta al territorio de El Salvador.
# Los datos del margen de 0.5° se conservan, pero no
# obligamos a que todo ese margen aparezca en la ventana.

margen_mapa = 0.05

ax.set_xlim(
    xmin - margen_mapa,
    xmax + margen_mapa
)

ax.set_ylim(
    ymin - margen_mapa,
    ymax + margen_mapa
)

# ------------------------------------------------------------
# 12. ASPECTO
# ------------------------------------------------------------

ax.set_xlabel("Longitud")
ax.set_ylabel("Latitud")

ax.grid(
    True,
    linewidth=0.3,
    alpha=0.25
)

ax.set_aspect("equal")


# ------------------------------------------------------------
# 13. GUARDAR
# ------------------------------------------------------------

plt.tight_layout()

plt.savefig(
    "/home/amides/mapas_lluvia/mapas/"
    "prueba_mapa_meteorologico.png",
    dpi=200,
    bbox_inches="tight"
)

plt.show()

# ============================================================
# 16. EXPORTAR GEOTIFF
# ============================================================

print("\n==========================================")
print("EXPORTANDO GEOTIFF")
print("==========================================")

# ------------------------------------------------------------
# Coordenadas de la matriz original recortada
# ------------------------------------------------------------

lon_tif = lluvia_el_salvador.longitude.values
lat_tif = lluvia_el_salvador.latitude.values

# Valores originales de precipitación
# NO usamos la interpolación visual
datos_tif = lluvia_el_salvador.values.astype("float32")


# ------------------------------------------------------------
# Resolución de la grilla
# ------------------------------------------------------------

res_lon = abs(
    float(lon_tif[1] - lon_tif[0])
)

res_lat = abs(
    float(lat_tif[1] - lat_tif[0])
)


# ------------------------------------------------------------
# Límites de la grilla
# ------------------------------------------------------------

xmin_tif = float(lon_tif.min())
xmax_tif = float(lon_tif.max())

ymin_tif = float(lat_tif.min())
ymax_tif = float(lat_tif.max())


# ------------------------------------------------------------
# Transformación espacial
# ------------------------------------------------------------

transform = from_bounds(
    xmin_tif - res_lon / 2,
    ymin_tif - res_lat / 2,
    xmax_tif + res_lon / 2,
    ymax_tif + res_lat / 2,
    len(lon_tif),
    len(lat_tif)
)


# ------------------------------------------------------------
# Nombre del archivo
# ------------------------------------------------------------

archivo_tif = (
    "/home/amides/mapas_lluvia/mapas/"
    f"precipitacion_"
    f"{inicio:%Y%m%d%H}_"
    f"{final:%Y%m%d%H}.tif"
)


# ------------------------------------------------------------
# Convertir NaN a NoData
# ------------------------------------------------------------

datos_tif = np.where(
    np.isnan(datos_tif),
    -9999.0,
    datos_tif
)


# ------------------------------------------------------------
# Crear GeoTIFF
# ------------------------------------------------------------

with rasterio.open(
    archivo_tif,
    "w",
    driver="GTiff",
    height=datos_tif.shape[0],
    width=datos_tif.shape[1],
    count=1,
    dtype="float32",
    crs="EPSG:4326",
    transform=transform,
    nodata=-9999.0,
    compress="deflate"
) as dst:

    dst.write(
        datos_tif,
        1
    )

    dst.set_band_description(
        1,
        "Precipitación acumulada (mm)"
    )

    dst.update_tags(
        units="mm",
        variable="Precipitación acumulada",
        modelos="GFS + IFS",
        fecha_corrida=str(corrida),
        fecha_inicio=str(inicio),
        fecha_final=str(final),
        peso_gfs=f"{peso_gfs} %",
        peso_ifs=f"{peso_ifs} %",
        resolucion="0.25 grados"
    )


print("\nGeoTIFF generado correctamente:")
print(archivo_tif)

print("\nResolución:")
print(f"  Longitud: {res_lon:.4f}°")
print(f"  Latitud : {res_lat:.4f}°")

print("\nDimensiones:")
print(f"  Filas   : {datos_tif.shape[0]}")
print(f"  Columnas: {datos_tif.shape[1]}")

print("\nCRS:")
print("  EPSG:4326")

print("\n==========================================")
print("TODOS LOS PRODUCTOS GENERADOS")
print("==========================================")

print("\nMapa guardado correctamente.")

print("\nMapa de prueba guardado en:")
print("/home/amides/mapas_lluvia/mapas/prueba_departamentos.png")
