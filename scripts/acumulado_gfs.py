from datetime import datetime
from herbie import Herbie


# ============================================================
# 1. DATOS DEL USUARIO
# ============================================================

fecha_corrida = input(
    "Fecha/hora de corrida GFS (YYYY-MM-DD HH:MM): "
)

fecha_inicio = input(
    "Fecha/hora inicial del acumulado (YYYY-MM-DD HH:MM): "
)

fecha_final = input(
    "Fecha/hora final del acumulado   (YYYY-MM-DD HH:MM): "
)


corrida = datetime.strptime(
    fecha_corrida, "%Y-%m-%d %H:%M"
)

inicio = datetime.strptime(
    fecha_inicio, "%Y-%m-%d %H:%M"
)

final = datetime.strptime(
    fecha_final, "%Y-%m-%d %H:%M"
)


# ============================================================
# 2. VALIDACIONES
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


# ============================================================
# 3. CALCULAR FORECASTS
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
        "respecto a la corrida GFS."
    )

if horas_final % 24 != 0:
    raise ValueError(
        "El final debe coincidir con un paso de 24 horas "
        "respecto a la corrida GFS."
    )


f_inicio = int(horas_inicio)
f_final = int(horas_final)


# ============================================================
# 4. MOSTRAR CONFIGURACIÓN
# ============================================================

print("\n==========================================")
print("CONFIGURACIÓN DEL ACUMULADO GFS")
print("==========================================")

print(f"Corrida GFS      : {corrida}")
print(f"Inicio acumulado : {inicio}")
print(f"Final acumulado  : {final}")

print(f"\nForecast inicial : F{f_inicio:03d}")
print(f"Forecast final   : F{f_final:03d}")


# ============================================================
# 5. FUNCIÓN PARA LEER APCP
# ============================================================

def leer_apcp(forecast):

    dias = forecast // 24

    print(
        f"\nDescargando GFS F{forecast:03d}..."
    )

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

    print(f"Variable : {apcp.name}")
    print(
        f"Unidades : "
        f"{apcp.attrs.get('GRIB_units', 'no disponibles')}"
    )

    print(
        f"Mínimo  : {float(apcp.min()):.2f} mm"
    )

    print(
        f"Máximo  : {float(apcp.max()):.2f} mm"
    )

    print(
        f"Promedio: {float(apcp.mean()):.2f} mm"
    )

    return apcp


# ============================================================
# 6. LEER LOS EXTREMOS DEL PERÍODO
# ============================================================

if f_inicio == 0:

    print("\nEl inicio del acumulado coincide con la corrida.")
    print("No es necesario descargar F000.")

    apcp_inicio = 0

else:

    apcp_inicio = leer_apcp(f_inicio)


apcp_final = leer_apcp(f_final)


# ============================================================
# 7. CALCULAR ACUMULADO
# ============================================================

if f_inicio == 0:

    acumulado = apcp_final

else:

    acumulado = (
        apcp_final - apcp_inicio
    ).clip(min=0)


# ============================================================
# 8. RESULTADOS
# ============================================================

print("\n==========================================")
print("RESULTADO")
print("==========================================")

print(
    f"Período: {inicio} → {final}"
)

print(
    f"Mínimo : {float(acumulado.min()):.2f} mm"
)

print(
    f"Máximo : {float(acumulado.max()):.2f} mm"
)

print(
    f"Promedio: {float(acumulado.mean()):.2f} mm"
)
