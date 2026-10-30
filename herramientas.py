import hashlib
import zipfile
import os

from pathlib import Path
from datetime import datetime
from contactos import ARCHIVO

INDICE = ARCHIVO.parent / "indice.json"
ARCHIVO_HASH = ARCHIVO.parent / "contactos.sha256"

CARPETA_RESPALDOS = Path(__file__).resolve().parent / "respaldos"


def calcular_hash(ruta):

    sha256 = hashlib.sha256()

    with open(ruta, "rb") as archivo:

        while True:

            bloque = archivo.read(4096)

            if not bloque:
                break

            sha256.update(bloque)

    return sha256.hexdigest()

def guardar_hash():

    if not ARCHIVO.exists():
        raise FileNotFoundError("El archivo de contactos no existe.")

    hash_actual = calcular_hash(ARCHIVO)

    ARCHIVO_HASH.parent.mkdir(parents=True, exist_ok=True)

    temporal = ARCHIVO_HASH.with_name(
        ARCHIVO_HASH.name + ".tmp"
    )

    with open(temporal, "w", encoding="utf-8") as archivo:
        archivo.write(hash_actual)

    os.replace(temporal, ARCHIVO_HASH)

    return hash_actual

def verificar_integridad():

    if not ARCHIVO.exists():
        raise FileNotFoundError("El archivo de contactos no existe.")

    if not ARCHIVO_HASH.exists():
        return None

    with open(ARCHIVO_HASH, "r", encoding="utf-8") as archivo:
        hash_original = archivo.read().strip()

    if (
        len(hash_original) != 64
        or any(c not in "0123456789abcdef" for c in hash_original)
    ):
        raise ValueError("El archivo SHA-256 está corrupto.")

    hash_actual = calcular_hash(ARCHIVO)

    return hash_original == hash_actual


def crear_respaldo():

    if not ARCHIVO.exists():
        raise FileNotFoundError("El archivo de contactos no existe.")

    if not INDICE.exists():
        raise FileNotFoundError("El archivo índice no existe.")

    integridad = verificar_integridad()

    if integridad is None:
        raise ValueError("Primero debe generarse el hash inicial.")

    if not integridad:
        raise ValueError(
            "No se puede crear el respaldo: el archivo fue modificado."
        )

    CARPETA_RESPALDOS.mkdir(parents=True, exist_ok=True)

    ruta_zip = CARPETA_RESPALDOS / "respaldo_contactos.zip"

    tamaño_original = (
        os.stat(ARCHIVO).st_size
        + os.stat(INDICE).st_size
    )


    with zipfile.ZipFile(
        ruta_zip,
        "w",
        compression=zipfile.ZIP_DEFLATED
    ) as zip_archivo:

        zip_archivo.write(ARCHIVO, arcname="contactos.dat")
        zip_archivo.write(INDICE, arcname="indice.json")

    tamaño_comprimido = os.stat(ruta_zip).st_size

    return ruta_zip, tamaño_original, tamaño_comprimido



def informacion_archivo():

    if not ARCHIVO.exists():
        raise FileNotFoundError("El archivo de contactos no existe.")

    informacion = os.stat(ARCHIVO)

    fecha = datetime.fromtimestamp(
        informacion.st_mtime
    ).strftime("%d/%m/%Y %H:%M:%S")

    lectura = os.access(ARCHIVO, os.R_OK)
    escritura = os.access(ARCHIVO, os.W_OK)

    return {
        "nombre": ARCHIVO.name,
        "tamaño": informacion.st_size,
        "fecha": fecha,
        "lectura": lectura,
        "escritura": escritura
    }



if __name__ == "__main__":

    try:

        print("----- VERIFICAR INTEGRIDAD SHA-256 -----")

        
        if not ARCHIVO_HASH.exists():

            print("No existe un hash de referencia.")

            respuesta = input(
                "¿Crear el hash inicial de los contactos actuales? (s/n): "
            )

            if respuesta.lower() == "s":

                hash_generado = guardar_hash()

                print("Hash inicial guardado correctamente.")
                print("SHA-256:", hash_generado)

        integridad = verificar_integridad()

        if integridad is True:
            print("Archivo íntegro: no se detectaron cambios.")

        elif integridad is False:
            print("ADVERTENCIA: El archivo fue modificado.")

        else:
            print("No existe un hash para verificar la integridad.")

        print("\n----- INFORMACIÓN DEL ARCHIVO -----")

        informacion = informacion_archivo()

        print("Nombre:", informacion["nombre"])
        print("Tamaño:", informacion["tamaño"], "bytes")
        print("Última modificación:", informacion["fecha"])
        print("Permiso de lectura:", informacion["lectura"])
        print("Permiso de escritura:", informacion["escritura"])

        print("\n----- CREAR RESPALDO ZIP -----")

        if integridad is True:

            ruta, original, comprimido = crear_respaldo()

            print("Respaldo creado correctamente.")
            print("Archivo:", ruta)
            print("Tamaño original:", original, "bytes")
            print("Tamaño comprimido:", comprimido, "bytes")

        else:
            print("No se creó el respaldo por falta de integridad verificada.")

    except (OSError, ValueError) as error:
        print("Error:", error)
