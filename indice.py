import json
from pathlib import Path

from contactos import (
    ARCHIVO,
    TAM_REGISTRO,
    agregar_contacto,
    leer_contacto,
    modificar_registro
)

from herramientas import (
    ARCHIVO_HASH,
    guardar_hash,
    verificar_integridad
)

INDICE = Path(__file__).resolve().parent / "datos" / "indice.json"


def cargar_indice():

    tamaño = ARCHIVO.stat().st_size if ARCHIVO.exists() else 0

    if tamaño % TAM_REGISTRO != 0:
        raise ValueError("El archivo de contactos tiene un tamaño inválido.")

    cantidad = tamaño // TAM_REGISTRO

    if not INDICE.exists():

        if cantidad > 0:
            raise ValueError(
                "Existen contactos, pero falta el índice JSON."
            )

        return {}

    try:
        with open(INDICE, "r", encoding="utf-8") as archivo:
            indice = json.load(archivo)

    except (json.JSONDecodeError, UnicodeError):
        raise ValueError("El archivo índice está corrupto.")

    if not isinstance(indice, dict):
        raise ValueError("El formato del índice no es válido.")

    if len(indice) != cantidad:
        raise ValueError(
            "El índice no coincide con la cantidad de contactos."
        )

    posiciones = []

    for codigo, numero in indice.items():

        if not codigo.isdecimal() or int(codigo) <= 0:
            raise ValueError("El índice contiene un ID inválido.")

        if type(numero) is not int or numero < 0:
            raise ValueError("El índice contiene una posición inválida.")

        posiciones.append(numero)

    if sorted(posiciones) != list(range(cantidad)):
        raise ValueError("Las posiciones del índice son incorrectas.")

    return indice


def guardar_indice(indice):

    INDICE.parent.mkdir(parents=True, exist_ok=True)

    temporal = INDICE.with_suffix(".tmp")

    with open(temporal, "w", encoding="utf-8") as archivo:

        json.dump(
            indice,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    temporal.replace(INDICE)


def comprobar_integridad():

    if not ARCHIVO.exists():

        if ARCHIVO_HASH.exists():
            raise ValueError(
                "Falta contactos.dat, pero existe un hash anterior."
            )

        return

    integridad = verificar_integridad()

    if integridad is False:
        raise ValueError(
            "ADVERTENCIA: El archivo de contactos fue modificado "
            "fuera de la aplicación."
        )

    if integridad is None and ARCHIVO.stat().st_size > 0:
        raise ValueError(
            "No existe el hash de referencia de los contactos."
        )


def registrar_contacto(id, nombre, telefono, correo, ciudad):

    indice = cargar_indice()

    codigo = str(id)

    if codigo in indice:
        raise ValueError("Ya existe un contacto con ese ID.")

    comprobar_integridad()

    numero = agregar_contacto(
        id, nombre, telefono, correo, ciudad
    )

    indice[codigo] = numero

    try:

        guardar_indice(indice)

        guardar_hash()

    except OSError:

        try:
            with open(ARCHIVO, "r+b") as archivo:
                archivo.truncate(numero * TAM_REGISTRO)

            indice.pop(codigo)
            guardar_indice(indice)

        except OSError as error_restauracion:
            raise RuntimeError(
                "No se pudo restaurar el registro. "
                "Revise los archivos antes de continuar."
            ) from error_restauracion

        raise

    return numero


def buscar_contacto_por_id(id):

    indice = cargar_indice()

    codigo = str(id)

    if codigo not in indice:
        return None

    numero = indice[codigo]

    contacto = leer_contacto(numero)

    if contacto is None or contacto["id"] != id:
        raise ValueError(
            "El índice no coincide con el contacto almacenado."
        )

    return contacto


def modificar_contacto_por_id(id, nombre, telefono, correo, ciudad):

    indice = cargar_indice()

    codigo = str(id)

    if codigo not in indice:
        return False


    comprobar_integridad()

    numero_registro = indice[codigo]

    contacto_anterior = leer_contacto(
        numero_registro,
        mostrar_posiciones=False
    )

    if contacto_anterior is None or contacto_anterior["id"] != id:
        raise ValueError("El índice no coincide con el contacto.")

    try:

        modificar_registro(
            numero_registro,
            id,
            nombre,
            telefono,
            correo,
            ciudad
        )

        guardar_hash()

    except OSError:

        try:
            modificar_registro(
                numero_registro,
                contacto_anterior["id"],
                contacto_anterior["nombre"],
                contacto_anterior["telefono"],
                contacto_anterior["correo"],
                contacto_anterior["ciudad"]
            )

        except OSError as error_restauracion:
            raise RuntimeError(
                "No se pudo restaurar el contacto anterior."
            ) from error_restauracion

        raise

    return True


def mostrar_contacto(contacto):

    etiquetas = {
        "id": "ID",
        "nombre": "Nombre",
        "telefono": "Teléfono",
        "correo": "Correo",
        "ciudad": "Ciudad"
    }

    for campo, valor in contacto.items():
        print(f"{etiquetas[campo]}: {valor}")


if __name__ == "__main__":

    try:

        print("----- VERIFICACIÓN INICIAL -----")

        estado = verificar_integridad()

        if estado is not True:
            raise ValueError(
                "No se puede continuar sin integridad verificada."
            )

        print("Archivo íntegro: no se detectaron cambios.")

        print("\n----- REGISTRAR NUEVO CONTACTO -----")

        if buscar_contacto_por_id(104) is None:

            numero = registrar_contacto(
                104,
                "Roberto Méndez",
                "5555-4321",
                "roberto@correo.com",
                "Quetzaltenango"
            )

            print("Contacto registrado en la posición:", numero)

        else:
            print("El contacto 104 ya está registrado.")

        print(
            "Integridad después de registrar:",
            verificar_integridad()
        )

        print("\n----- MODIFICAR CONTACTO -----")

        modificado = modificar_contacto_por_id(
            102,
            "Carlos Pérez",
            "5555-8888",
            "carlos.nuevo@correo.com",
            "Guatemala"
        )

        if modificado:
            print("Contacto modificado correctamente.")
        else:
            print("Contacto no encontrado.")

        print("\n----- VERIFICAR CONTACTO -----")

        contacto = buscar_contacto_por_id(102)

        if contacto is not None:
            mostrar_contacto(contacto)

        print("\n----- VERIFICACIÓN FINAL SHA-256 -----")

        if verificar_integridad() is True:
            print("Archivo íntegro: SHA-256 actualizado correctamente.")
        else:
            print("ADVERTENCIA: La integridad no coincide.")

    except (OSError, ValueError, RuntimeError) as error:
        print("Error:", error)
