from datetime import datetime
from herbie import Herbie


# ============================================================
# 1. DATOS DEL USUARIO
# ============================================================

fecha_corrida = input(
    "Fecha/hora de corrida IFS (YYYY-MM-DD HH:MM): "
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
# 3. CALCULAR HORAS DESDE LA CORRIDA
# ============================================================

horas_inicio = (
    inicio - corrida
).total_seconds() / 3600

horas_final = (
    final - corrida
).total_seconds() / 3600


# Para este primer producto trabajaremos con pasos de 24 horas

if horas_inicio % 24 != 0:
    raise ValueError(
        "El inicio debe coincidir con un paso de 24 horas "
        "respecto a la corrida IFS."
    )

if horas_final % 24 != 0:
    raise ValueError(
        "El final debe coincidir con un paso de 24 horas "
        "respecto a la corrida IFS."
    )


f_inicio = int(horas_inicio)
f_final = int(horas_final)


# ============================================================
# 4. MOSTRAR LO QUE CALCULÓ EL PROGRAMA
# ============================================================

print("\n==========================================")
print("CONFIGURACIÓN DEL ACUMULADO")
print("==========================================")

print(f"Corrida IFS       : {corrida}")
print(f"Inicio acumulado  : {inicio}")
print(f"Final acumulado   : {final}")

print(f"\nForecast inicial  : F{f_inicio:03d}")
print(f"Forecast final    : F{f_final:03d}")


# ============================================================
# 5. FUNCIÓN PARA LEER TP
# ============================================================

def leer_tp(forecast):

    print(
        f"\nDescargando IFS F{forecast:03d}..."
    )

    H = Herbie(
        corrida,
        model="ifs",
        product="oper",
        fxx=forecast
    )

    ds = H.xarray(":tp:")

    tp = ds["tp"]

    # IFS entrega tp en metros
    tp_mm = tp * 1000

    print(
        f"Máximo F{forecast:03d}: "
        f"{float(tp_mm.max()):.2f} mm"
    )

    return tp_mm


# ============================================================
# 6. LEER LOS DOS EXTREMOS DEL PERÍODO
# ============================================================

if f_inicio == 0:

    print("\nEl inicio del acumulado coincide con la corrida.")
    print("No es necesario descargar F000.")

    tp_inicio = 0

else:

    tp_inicio = leer_tp(f_inicio)


tp_final = leer_tp(f_final)


# ============================================================
# 7. CALCULAR ACUMULADO
# ============================================================

if f_inicio == 0:

    acumulado = tp_final

else:

    acumulado = (
        tp_final - tp_inicio
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
