import json
from pathlib import Path

from contactos import ARCHIVO, TAM_REGISTRO
from contactos import agregar_contacto, leer_contacto


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

    # Verificamos que las posiciones sean válidas.
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


def registrar_contacto(id, nombre, telefono, correo, ciudad):

    indice = cargar_indice()

    codigo = str(id)

    if codigo in indice:
        raise ValueError("Ya existe un contacto con ese ID.")

    numero = agregar_contacto(
        id, nombre, telefono, correo, ciudad
    )

    indice[codigo] = numero

    try:
        guardar_indice(indice)

    except OSError:
        with open(ARCHIVO, "r+b") as archivo:
            archivo.truncate(numero * TAM_REGISTRO)

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


if __name__ == "__main__":

    print("----- REGISTRAR CONTACTOS -----")

    contactos_prueba = [
        (101, "Ana López", "5555-1234",
         "ana@correo.com", "Quetzaltenango"),

        (102, "Carlos Pérez", "5555-5678",
         "carlos@correo.com", "Guatemala"),

        (103, "María García", "5555-9012",
         "maria@correo.com", "Antigua Guatemala")
    ]

    for id, nombre, telefono, correo, ciudad in contactos_prueba:

        if buscar_contacto_por_id(id) is None:

            numero = registrar_contacto(
                id, nombre, telefono, correo, ciudad
            )

            print(f"Contacto {id} guardado en el registro {numero}")

        else:
            print(f"El contacto {id} ya está registrado.")

    print("\n----- BUSCAR CONTACTO POR ID -----")

    contacto = buscar_contacto_por_id(103)

    if contacto is not None:

        etiquetas = {
            "id": "ID",
            "nombre": "Nombre",
            "telefono": "Teléfono",
            "correo": "Correo",
            "ciudad": "Ciudad"
        }

        for campo, valor in contacto.items():
            print(f"{etiquetas[campo]}: {valor}")

    else:
        print("Contacto no encontrado.")


    print("\n----- BUSCAR ID INEXISTENTE -----")

    contacto = buscar_contacto_por_id(999)

    if contacto is None:
        print("El contacto con ID 999 no existe.")

    print("\n----- ÍNDICE ACTUAL -----")

    print(json.dumps(cargar_indice(), indent=4))
