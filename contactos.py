
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

    if not isinstance(id, int) or isinstance(id, bool):
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
        "ID": int(leer_campo(TAM_ID)),
        "Nombre": leer_campo(TAM_NOMBRE),
        "Teléfono": leer_campo(TAM_TELEFONO),
        "Correo": leer_campo(TAM_CORREO),
        "Ciudad": leer_campo(TAM_CIUDAD)
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


def leer_contacto(numero_registro):

    if numero_registro < 0:
        raise ValueError("Número de registro inválido.")

    if not ARCHIVO.exists():
        raise FileNotFoundError("El archivo de contactos no existe.")

    posicion = numero_registro * TAM_REGISTRO

    with open(ARCHIVO, "rb") as archivo:

        archivo.seek(posicion)

        print("Posición inicial con tell():", archivo.tell())

        datos = archivo.read(TAM_REGISTRO)

        if not datos:
            return None

        print("Posición final con tell():", archivo.tell())

        return convertir_registro(datos)


if __name__ == "__main__":

    print("Tamaño de registro:", TAM_REGISTRO, "bytes")

    numero = agregar_contacto(
        101,
        "Ana López",
        "5555-1234",
        "ana@correo.com",
        "Quetzaltenango"
    )

    print("Contacto guardado en el registro:", numero)

    contacto = leer_contacto(numero)

    print("\nCONTACTO ENCONTRADO:")

    for campo, valor in contacto.items():
        print(f"{campo}: {valor}")
