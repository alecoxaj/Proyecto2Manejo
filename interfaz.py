from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QFormLayout, QDialog, QMessageBox,
    QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)

from contactos import ARCHIVO, crear_registro, leer_contacto
from indice import (
    cargar_indice, registrar_contacto, buscar_contacto_por_id,
    modificar_contacto_por_id
)
from exportación import exportar_contactos_json, generar_reporte_pdf
from herramientas import (
    ARCHIVO_HASH, verificar_integridad, crear_respaldo, informacion_archivo
)


ESTILO = """
QWidget { font-family: 'Segoe UI'; font-size: 13px; color: #23324B; }
QWidget#fondo { background-color: #F3F6FB; }
QFrame#lateral { background-color: #14233F; }
QLabel#marca { color: white; font-size: 22px; font-weight: 700; }
QLabel#marcaSub { color: #AFC0DB; font-size: 12px; }
QPushButton[menu="true"] {
    color: #C4D1E5; background: transparent; text-align: left;
    border: none; border-radius: 11px; padding: 13px 16px;
    font-size: 14px; font-weight: 600;
}
QPushButton[menu="true"]:hover { background: #223858; color: white; }
QPushButton[menu="true"]:checked { background: #3157B7; color: white; }
QLabel#titulo { font-size: 27px; font-weight: 700; color: #182844; }
QLabel#subtitulo { color: #71809A; font-size: 13px; }
QLabel#nota { color: #63738D; font-size: 12px; }
QFrame#tarjeta { background: white; border: 1px solid #E2E8F2; border-radius: 16px; }
QLabel#tarjetaTitulo { font-size: 18px; font-weight: 700; color: #243657; }
QLineEdit {
    background: white; border: 1px solid #D7E0EC; border-radius: 9px;
    padding: 10px 12px; min-height: 20px;
}
QLineEdit:focus { border: 1px solid #3467D6; }
QLineEdit:read-only { background: #F1F4F8; color: #63738D; }
QPushButton#primario {
    background: #3466D3; color: white; border: none;
    border-radius: 9px; padding: 12px 16px; font-weight: 700;
}
QPushButton#primario:hover { background: #244FB1; }
QPushButton#secundario {
    background: #EDF2FC; color: #284A89; border: none;
    border-radius: 9px; padding: 12px 16px; font-weight: 600;
}
QPushButton#secundario:hover { background: #DBE7FC; }
QTableWidget {
    background: white; border: none; gridline-color: #E7ECF4;
    alternate-background-color: #F6F8FC; selection-background-color: #DCE8FF;
    selection-color: #18305B;
}
QHeaderView::section {
    background: #EEF3FA; color: #4C5E7C; border: none;
    border-bottom: 1px solid #DCE4EF; padding: 11px;
    font-weight: 700;
}
QTableWidget::item { padding: 7px; }
QDialog { background: #F8FAFE; }
"""


def boton(texto, tipo="secundario"):
    resultado = QPushButton(texto)
    resultado.setObjectName(tipo)
    resultado.setCursor(Qt.PointingHandCursor)
    return resultado


class FormularioContacto(QDialog):
    def __init__(self, parent=None, contacto=None):
        super().__init__(parent)
        self.setWindowTitle("Modificar contacto" if contacto else "Agregar contacto")
        self.setMinimumWidth(440)

        contenedor = QVBoxLayout(self)
        contenedor.setContentsMargins(26, 25, 26, 25)
        contenedor.setSpacing(16)

        encabezado = QLabel("Modificar contacto" if contacto else "Nuevo contacto")
        encabezado.setObjectName("tarjetaTitulo")
        contenedor.addWidget(encabezado)

        formulario = QFormLayout()
        formulario.setSpacing(13)
        self.campos = {}

        etiquetas = (
            ("id", "ID"), ("nombre", "Nombre"),
            ("telefono", "Teléfono"), ("correo", "Correo"),
            ("ciudad", "Ciudad")
        )

        for clave, etiqueta in etiquetas:
            entrada = QLineEdit()
            entrada.setPlaceholderText(f"Ingresa {etiqueta.lower()}")
            if contacto:
                entrada.setText(str(contacto[clave]))
            if clave == "id" and contacto:
                entrada.setReadOnly(True)
            self.campos[clave] = entrada
            formulario.addRow(etiqueta + ":", entrada)

        contenedor.addLayout(formulario)

        acciones = QHBoxLayout()
        acciones.addStretch()
        cancelar = boton("Cancelar")
        guardar = boton("Guardar contacto", "primario")
        cancelar.clicked.connect(self.reject)
        guardar.clicked.connect(self.validar)
        acciones.addWidget(cancelar)
        acciones.addWidget(guardar)
        contenedor.addLayout(acciones)

    def datos(self):
        datos = {clave: entrada.text().strip()
                 for clave, entrada in self.campos.items()}
        if not datos["id"].isdigit():
            raise ValueError("El ID debe ser un número entero positivo.")
        datos["id"] = int(datos["id"])

        crear_registro(
            datos["id"], datos["nombre"], datos["telefono"],
            datos["correo"], datos["ciudad"]
        )
        return datos

    def validar(self):
        try:
            self.datos()
        except (ValueError, UnicodeError) as error:
            QMessageBox.warning(self, "Datos inválidos", str(error))
            return
        self.accept()


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agenda de Contactos")
        self.resize(1180, 740)
        self.setMinimumSize(960, 620)

        fondo = QWidget()
        fondo.setObjectName("fondo")
        self.setCentralWidget(fondo)
        principal = QHBoxLayout(fondo)
        principal.setContentsMargins(0, 0, 0, 0)
        principal.setSpacing(0)

        lateral = QFrame()
        lateral.setObjectName("lateral")
        lateral.setFixedWidth(238)
        barra = QVBoxLayout(lateral)
        barra.setContentsMargins(18, 32, 18, 22)
        barra.setSpacing(9)

        marca = QLabel("Agenda de Contactos")
        marca.setObjectName("marca")
        marca.setWordWrap(True)
        barra.addWidget(marca)
        barra.addSpacing(30)

        self.navegacion = []
        opciones = (
            "◉   Contactos", "▤   Exportar",
            "⚙   Herramientas", "?   Ayuda"
        )
        for numero, texto in enumerate(opciones):
            entrada = QPushButton(texto)
            entrada.setProperty("menu", True)
            entrada.setCheckable(True)
            entrada.setCursor(Qt.PointingHandCursor)
            entrada.clicked.connect(
                lambda _marcado=False, indice=numero: self.mostrar_pagina(indice)
            )
            barra.addWidget(entrada)
            self.navegacion.append(entrada)

        barra.addStretch()
        pie = QLabel("Agenda con acceso aleatorio\nRegistros de 152 bytes")
        pie.setObjectName("marcaSub")
        barra.addWidget(pie)
        principal.addWidget(lateral)

        self.paginas = QStackedWidget()
        principal.addWidget(self.paginas, 1)
        self.paginas.addWidget(self.pagina_contactos())
        self.paginas.addWidget(self.pagina_exportar())
        self.paginas.addWidget(self.pagina_herramientas())
        self.paginas.addWidget(self.pagina_ayuda())
        self.mostrar_pagina(0)
        self.actualizar_tabla(avisar=False)

    def nueva_pagina(self, titulo, descripcion):
        pagina = QWidget()
        columna = QVBoxLayout(pagina)
        columna.setContentsMargins(32, 30, 32, 30)
        columna.setSpacing(18)
        encabezado = QLabel(titulo)
        encabezado.setObjectName("titulo")
        columna.addWidget(encabezado)
        texto = QLabel(descripcion)
        texto.setObjectName("subtitulo")
        texto.setWordWrap(True)
        columna.addWidget(texto)
        return pagina, columna

    def tarjeta(self, titulo, detalle):
        marco = QFrame()
        marco.setObjectName("tarjeta")
        contenido = QVBoxLayout(marco)
        contenido.setContentsMargins(23, 22, 23, 22)
        contenido.setSpacing(13)
        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("tarjetaTitulo")
        contenido.addWidget(etiqueta)
        descripcion = QLabel(detalle)
        descripcion.setObjectName("subtitulo")
        descripcion.setWordWrap(True)
        contenido.addWidget(descripcion)
        return marco, contenido

    def pagina_contactos(self):
        pagina, columna = self.nueva_pagina(
            "Contactos", "Administra tus contactos mediante registros fijos e índice JSON."
        )
        panel, contenido = self.tarjeta(
            "Directorio", "Busca un contacto por su ID o consulta el listado completo."
        )

        controles = QHBoxLayout()
        controles.setSpacing(8)
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Buscar por ID...")
        self.busqueda.returnPressed.connect(self.buscar_id)
        controles.addWidget(self.busqueda, 1)

        buscar = boton("Buscar")
        mostrar = boton("Mostrar todos")
        agregar = boton("+ Agregar", "primario")
        buscar.clicked.connect(self.buscar_id)
        mostrar.clicked.connect(lambda: self.actualizar_tabla())
        agregar.clicked.connect(self.agregar_contacto)
        for control in (buscar, mostrar, agregar):
            controles.addWidget(control)
        contenido.addLayout(controles)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Teléfono", "Correo", "Ciudad"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.verticalHeader().hide()
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.cellDoubleClicked.connect(self.modificar_contacto)
        contenido.addWidget(self.tabla, 1)

        acciones = QHBoxLayout()
        self.contador = QLabel("0 contactos")
        self.contador.setObjectName("nota")
        acciones.addWidget(self.contador)
        acciones.addStretch()
        editar = boton("Modificar seleccionado", "primario")
        editar.clicked.connect(self.modificar_contacto)
        acciones.addWidget(editar)
        contenido.addLayout(acciones)
        columna.addWidget(panel, 1)
        return pagina

    def pagina_exportar(self):
        pagina, columna = self.nueva_pagina(
            "Exportar", "Genera archivos de intercambio y reportes de tus contactos."
        )
        panel_json, contenido_json = self.tarjeta(
            "Exportar a JSON", "Guarda todos los contactos en reportes/contactos.json."
        )
        accion_json = boton("Exportar JSON", "primario")
        accion_json.clicked.connect(self.exportar_json)
        contenido_json.addWidget(accion_json, alignment=Qt.AlignLeft)
        columna.addWidget(panel_json)

        panel_pdf, contenido_pdf = self.tarjeta(
            "Generar reporte PDF",
            "Primero actualiza el JSON y después crea el PDF con fecha y tabla de contactos."
        )
        accion_pdf = boton("Generar PDF", "primario")
        accion_pdf.clicked.connect(self.exportar_pdf)
        contenido_pdf.addWidget(accion_pdf, alignment=Qt.AlignLeft)
        columna.addWidget(panel_pdf)
        columna.addStretch()
        return pagina

    def pagina_herramientas(self):
        pagina, columna = self.nueva_pagina(
            "Herramientas", "Comprueba la integridad, crea respaldos y consulta información del archivo."
        )
        opciones = (
            ("Verificar integridad SHA-256",
             "Compara contactos.dat con el hash de referencia.",
             "Verificar integridad", self.comprobar_hash),
            ("Respaldo comprimido ZIP",
             "Guarda contactos.dat e indice.json en un archivo ZIP.",
             "Crear respaldo", self.respaldar),
            ("Información del archivo",
             "Consulta tamaño, fecha de modificación y permisos.",
             "Ver información", self.informacion)
        )
        for titulo, descripcion, texto_boton, accion in opciones:
            panel, contenido = self.tarjeta(titulo, descripcion)
            control = boton(texto_boton, "primario")
            control.clicked.connect(accion)
            contenido.addWidget(control, alignment=Qt.AlignLeft)
            columna.addWidget(panel)
        columna.addStretch()
        return pagina

    def pagina_ayuda(self):
        pagina, columna = self.nueva_pagina(
            "Ayuda", "Información general de la agenda de contactos."
        )
        panel, contenido = self.tarjeta(
            "Acerca de la aplicación",
            "Aplicación académica de escritorio desarrollada en Python y PySide6."
        )
        explicacion = QLabel(
            "Contactos: agrega, busca y modifica registros.\n\n"
            "Exportar: genera JSON y PDF.\n\n"
            "Herramientas: verifica SHA-256, crea un ZIP y consulta metadatos.\n\n"
            "Sección de ayuda informativa (simulada según el laboratorio)."
        )
        explicacion.setWordWrap(True)
        contenido.addWidget(explicacion)
        columna.addWidget(panel)
        columna.addStretch()
        return pagina

    def mostrar_pagina(self, numero):
        self.paginas.setCurrentIndex(numero)
        for indice, control in enumerate(self.navegacion):
            control.setChecked(indice == numero)

    def mostrar_error(self, error):
        if isinstance(error, PermissionError):

            QMessageBox.critical(
                self,
                "Permiso denegado",
                "No se pudo completar la operación porque el archivo "
                "no tiene los permisos necesarios de lectura o escritura.\n\n"
                "Verifica que contactos.dat no esté configurado "
                "como 'Solo lectura'."
            )

        else:
            QMessageBox.critical(
                self,
                "Error",
                str(error)
            )

    def colocar_contactos(self, contactos):
        self.tabla.setRowCount(len(contactos))
        for fila, contacto in enumerate(contactos):
            valores = (
                contacto["id"], contacto["nombre"], contacto["telefono"],
                contacto["correo"], contacto["ciudad"]
            )
            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.tabla.setItem(fila, columna, item)
        self.contador.setText(f"{len(contactos)} contacto(s) en pantalla")

    def actualizar_tabla(self, avisar=True):
        try:
            indice = cargar_indice()
            contactos = []
            for codigo, numero_registro in sorted(
                indice.items(), key=lambda par: par[1]
            ):
                contacto = leer_contacto(
                    numero_registro, mostrar_posiciones=False
                )
                if contacto is None or str(contacto["id"]) != codigo:
                    raise ValueError("El índice no coincide con los contactos.")
                contactos.append(contacto)
            self.colocar_contactos(contactos)
            self.busqueda.clear()
        except Exception as error:
            self.colocar_contactos([])
            if avisar:
                self.mostrar_error(error)

    def buscar_id(self):
        texto = self.busqueda.text().strip()
        if not texto:
            self.actualizar_tabla()
            return
        if not texto.isdigit():
            QMessageBox.warning(self, "ID inválido", "Ingresa un ID numérico.")
            return
        try:
            contacto = buscar_contacto_por_id(int(texto))
            if contacto is None:
                self.colocar_contactos([])
                QMessageBox.information(self, "Sin resultados", "El ID no existe.")
            else:
                self.colocar_contactos([contacto])
                self.tabla.selectRow(0)
        except Exception as error:
            self.mostrar_error(error)

    def agregar_contacto(self):
        formulario = FormularioContacto(self)
        if formulario.exec() != QDialog.Accepted:
            return
        try:
            registrar_contacto(**formulario.datos())
            self.actualizar_tabla()
            QMessageBox.information(self, "Registro completo", "Contacto agregado correctamente.")
        except Exception as error:
            self.mostrar_error(error)

    def modificar_contacto(self, *_):
        fila = self.tabla.currentRow()

        if fila < 0:
            QMessageBox.warning(
                self,
                "Seleccionar contacto",
                "Primero selecciona un contacto de la tabla."
            )
            return

        try:
            id_contacto = int(self.tabla.item(fila, 0).text())

            contacto = buscar_contacto_por_id(id_contacto)

            if contacto is None:
                raise ValueError("El contacto ya no existe.")

            formulario = FormularioContacto(self, contacto)

            if formulario.exec() != QDialog.Accepted:
                return

            nuevos_datos = formulario.datos()

            if contacto == nuevos_datos:
                QMessageBox.information(
                    self,
                    "Sin cambios",
                    "No se detectaron cambios en la información del contacto."
                )
                return

            modificado = modificar_contacto_por_id(**nuevos_datos)

            if modificado:

                self.actualizar_tabla()

                QMessageBox.information(
                    self,
                    "Cambios guardados",
                    "Contacto modificado correctamente."
                )

            else:
                QMessageBox.warning(
                    self,
                    "Contacto no encontrado",
                    "El contacto ya no existe."
                )

        except Exception as error:
            self.mostrar_error(error)

    def exportar_json(self):
        try:
            ruta = exportar_contactos_json()
            QMessageBox.information(self, "Exportación completada", f"JSON generado en:\n{ruta}")
        except Exception as error:
            self.mostrar_error(error)

    def exportar_pdf(self):
        try:
            exportar_contactos_json()
            ruta = generar_reporte_pdf()
            QMessageBox.information(self, "Reporte generado", f"PDF guardado en:\n{ruta}")
        except Exception as error:
            self.mostrar_error(error)

    def comprobar_hash(self):
        try:
            if not ARCHIVO.exists():
                mensaje = "No existe todavía el archivo de contactos."
            else:
                resultado = verificar_integridad()
                if resultado is True:
                    mensaje = "Archivo íntegro: no se detectaron cambios."
                elif resultado is False:
                    mensaje = "ADVERTENCIA: el archivo fue modificado fuera de la aplicación."
                else:
                    mensaje = "No existe un hash de referencia para verificar los datos."
            QMessageBox.information(self, "Integridad SHA-256", mensaje)
        except Exception as error:
            self.mostrar_error(error)

    def respaldar(self):
        try:
            ruta, original, comprimido = crear_respaldo()
            mensaje = (
                f"Respaldo creado correctamente.\n\n"
                f"Archivo: {ruta}\n"
                f"Tamaño original: {original} bytes\n"
                f"Tamaño ZIP: {comprimido} bytes"
            )
            QMessageBox.information(self, "Respaldo ZIP", mensaje)
        except Exception as error:
            self.mostrar_error(error)

    def informacion(self):
        try:
            datos = informacion_archivo()
            mensaje = (
                f"Archivo: {datos['nombre']}\n"
                f"Tamaño: {datos['tamaño']} bytes\n"
                f"Última modificación: {datos['fecha']}\n"
                f"Lectura: {'Sí' if datos['lectura'] else 'No'}\n"
                f"Escritura: {'Sí' if datos['escritura'] else 'No'}"
            )
            QMessageBox.information(self, "Información del archivo", mensaje)
        except Exception as error:
            self.mostrar_error(error)

    def verificar_integridad_al_inicio(self):
        try:

            cargar_indice()
            if not ARCHIVO.exists():
                if ARCHIVO_HASH.exists():
                    QMessageBox.warning(
                        self, "Atención", "Falta contactos.dat, pero existe un hash anterior."
                    )
                return
            resultado = verificar_integridad()
            if resultado is False:
                QMessageBox.warning(
                    self, "Advertencia de integridad",
                    "contactos.dat fue modificado fuera de la aplicación. "
                    "No se permitirán nuevos cambios hasta revisar los archivos."
                )
            elif resultado is None and ARCHIVO.stat().st_size > 0:
                QMessageBox.warning(
                    self, "Falta SHA-256",
                    "No existe el hash de referencia. Revise los archivos antes de guardar."
                )
        except Exception as error:
            self.mostrar_error(error)
