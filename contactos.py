from pathlib import Path

ARCHIVO = Path(__file__).resolve().parent / "datos" / "contactos.dat"

TAM_ID = 8
TAM_NOMBRE = 40
TAM_TELEFONO = 18
TAM_CORREO = 50
TAM_CIUDAD = 35

TAM_REGISTRO = 152


def ajustar_campo(valor, tamaño):

    texto = str(valor).strip()

    if not texto or "\n" in texto or "\r" in texto:
        raise ValueError("El campo contiene un valor inválido.")

    datos = texto.encode("utf-8")

    if len(datos) > tamaño:
        raise ValueError(
            f"El campo supera el máximo de {tamaño} bytes."
        )

    return datos.ljust(tamaño, b" ")


def crear_registro(id, nombre, telefono, correo, ciudad):

    if type(id) is not int:
        raise ValueError("El ID debe ser un número entero.")

    if id < 1 or id > 99999999:
        raise ValueError("El ID debe tener entre 1 y 8 dígitos.")

    registro = (
        str(id).zfill(TAM_ID).encode("ascii")
        + ajustar_campo(nombre, TAM_NOMBRE)
        + ajustar_campo(telefono, TAM_TELEFONO)
        + ajustar_campo(correo, TAM_CORREO)
        + ajustar_campo(ciudad, TAM_CIUDAD)
        + b"\n"
    )

    return registro


def convertir_registro(datos):

    if len(datos) != TAM_REGISTRO or not datos.endswith(b"\n"):
        raise ValueError("El registro está incompleto o corrupto.")

    posicion = 0

    def leer_campo(tamaño):
        nonlocal posicion

        campo = datos[posicion:posicion + tamaño]
        posicion += tamaño

        return campo.decode("utf-8").strip()

    return {
        "id": int(leer_campo(TAM_ID)),
        "nombre": leer_campo(TAM_NOMBRE),
        "telefono": leer_campo(TAM_TELEFONO),
        "correo": leer_campo(TAM_CORREO),
        "ciudad": leer_campo(TAM_CIUDAD)
    }


def agregar_contacto(id, nombre, telefono, correo, ciudad):

    registro = crear_registro(
        id, nombre, telefono, correo, ciudad
    )

    ARCHIVO.parent.mkdir(parents=True, exist_ok=True)

    with open(ARCHIVO, "a+b") as archivo:

        archivo.seek(0, 2)
        posicion = archivo.tell()

        if posicion % TAM_REGISTRO != 0:
            raise ValueError("El archivo tiene un tamaño inválido.")

        numero_registro = posicion // TAM_REGISTRO

        archivo.write(registro)

    return numero_registro


def leer_contacto(numero_registro, mostrar_posiciones=True):

    if type(numero_registro) is not int or numero_registro < 0:
        raise ValueError("Número de registro inválido.")

    if not ARCHIVO.exists():
        raise FileNotFoundError("El archivo de contactos no existe.")

    posicion = numero_registro * TAM_REGISTRO

    with open(ARCHIVO, "rb") as archivo:

        archivo.seek(posicion)

        if mostrar_posiciones:
            print("Posición inicial con tell():", archivo.tell())

        datos = archivo.read(TAM_REGISTRO)

        if not datos:
            return None

        if mostrar_posiciones:
            print("Posición final con tell():", archivo.tell())

        return convertir_registro(datos)


def modificar_registro(numero_registro, id, nombre, telefono, correo, ciudad):

    if type(numero_registro) is not int or numero_registro < 0:
        raise ValueError("Número de registro inválido.")

    nuevos_datos = crear_registro(
        id, nombre, telefono, correo, ciudad
    )

    posicion = numero_registro * TAM_REGISTRO

    with open(ARCHIVO, "r+b") as archivo:

        archivo.seek(0, 2)
        tamaño_total = archivo.tell()

        if tamaño_total % TAM_REGISTRO != 0:
            raise ValueError("El archivo tiene un tamaño inválido.")

        if posicion + TAM_REGISTRO > tamaño_total:
            raise ValueError("El registro no existe.")

        archivo.seek(posicion)

        datos_actuales = archivo.read(TAM_REGISTRO)

        contacto_actual = convertir_registro(datos_actuales)

        if contacto_actual["id"] != id:
            raise ValueError("El ID no coincide con el registro.")

        archivo.seek(posicion)

        print("Posición inicial con tell():", archivo.tell())

        archivo.write(nuevos_datos)

        print("Posición final con tell():", archivo.tell())

    return True
