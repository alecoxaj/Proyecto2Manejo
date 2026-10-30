import json
from pathlib import Path
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)

from contactos import ARCHIVO, TAM_REGISTRO, convertir_registro
from indice import cargar_indice

CARPETA_REPORTES = Path(__file__).resolve().parent / "reportes"

ARCHIVO_JSON = CARPETA_REPORTES / "contactos.json"
ARCHIVO_PDF = CARPETA_REPORTES / "reporte_contactos.pdf"


def exportar_contactos_json():

    contactos = []

    indice = cargar_indice()

    if ARCHIVO.exists():

        with open(ARCHIVO, "rb") as archivo:

            numero_registro = 0

            while True:

                datos = archivo.read(TAM_REGISTRO)

                if not datos:
                    break

                contacto = convertir_registro(datos)

                codigo = str(contacto["id"])

                if indice.get(codigo) != numero_registro:
                    raise ValueError(
                        "El índice no coincide con los contactos."
                    )

                contactos.append(contacto)

                numero_registro += 1

    if len(contactos) != len(indice):
        raise ValueError(
            "La cantidad de contactos no coincide con el índice."
        )

    CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)

    with open(ARCHIVO_JSON, "w", encoding="utf-8") as archivo:

        json.dump(
            contactos,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    print("Contactos exportados correctamente a JSON.")
    print("Cantidad de contactos:", len(contactos))

    return ARCHIVO_JSON


def generar_reporte_pdf():

    if not ARCHIVO_JSON.exists():
        raise FileNotFoundError(
            "Primero debe exportar los contactos a JSON."
        )

    with open(ARCHIVO_JSON, "r", encoding="utf-8") as archivo:
        contactos = json.load(archivo)

    if not isinstance(contactos, list):
        raise ValueError("El archivo JSON tiene un formato inválido.")

    pdf = SimpleDocTemplate(
        str(ARCHIVO_PDF),
        pagesize=landscape(A4),
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    estilos = getSampleStyleSheet()

    estilo_celda = ParagraphStyle(
        "CeldaContacto",
        fontName="Helvetica",
        fontSize=8,
        leading=11
    )

    elementos = []

    titulo = Paragraph(
        "REPORTE DE CONTACTOS",
        estilos["Title"]
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 15))

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    elementos.append(
        Paragraph(
            f"Fecha de generación: {fecha}",
            estilos["Normal"]
        )
    )

    elementos.append(Spacer(1, 8))

    elementos.append(
        Paragraph(
            f"Total de contactos: {len(contactos)}",
            estilos["Normal"]
        )
    )

    elementos.append(Spacer(1, 20))

    if contactos:

        datos_tabla = [
            ["ID", "Nombre", "Teléfono", "Correo", "Ciudad"]
        ]

        for contacto in contactos:

            fila = [
                contacto["id"],
                contacto["nombre"],
                contacto["telefono"],
                contacto["correo"],
                contacto["ciudad"]
            ]

            datos_tabla.append([
                Paragraph(
                    escape(str(valor)),
                    estilo_celda
                )
                for valor in fila
            ])

        tabla = Table(
            datos_tabla,
            colWidths=[45, 170, 110, 250, 130],
            repeatRows=1
        )

        tabla.setStyle(TableStyle([

            ("BACKGROUND", (0, 0), (-1, 0),
             colors.HexColor("#203864")),

            ("TEXTCOLOR", (0, 0), (-1, 0),
             colors.white),

            ("FONTNAME", (0, 0), (-1, 0),
             "Helvetica-Bold"),

            ("FONTSIZE", (0, 0), (-1, 0), 10),

            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F1F5F9")]),

            ("GRID", (0, 0), (-1, -1),
             0.4, colors.lightgrey),

            ("VALIGN", (0, 0), (-1, -1), "TOP"),

            ("TOPPADDING", (0, 0), (-1, -1), 8),

            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

        ]))

        elementos.append(tabla)

    else:
        elementos.append(
            Paragraph(
                "No hay contactos registrados.",
                estilos["Normal"]
            )
        )

    pdf.build(elementos)

    print("Reporte PDF generado correctamente.")

    return ARCHIVO_PDF

if __name__ == "__main__":

    try:

        print("----- EXPORTAR CONTACTOS A JSON -----")

        ruta_json = exportar_contactos_json()

        print("Archivo generado:", ruta_json)

        print("\n----- GENERAR REPORTE PDF -----")

        ruta_pdf = generar_reporte_pdf()

        print("Archivo generado:", ruta_pdf)

    except (OSError, ValueError, UnicodeError,
            json.JSONDecodeError) as error:

        print("Error:", error)
