import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from interfaz import VentanaPrincipal, ESTILO


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(ESTILO)

    ventana = VentanaPrincipal()
    ventana.show()

    QTimer.singleShot(0, ventana.verificar_integridad_al_inicio)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
