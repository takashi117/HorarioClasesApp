import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import VentanaPrincipal
import database
import engine

def main():
    # 1. Asegurar que la base de datos existe
    database.inicializar_db()
    
    # 2. Iniciar la aplicacion grafica
    app = QApplication(sys.argv)
    
    # Estilo basico (Fusion es limpio y estandar)
    app.setStyle("Fusion")
    
    ventana = VentanaPrincipal()
    ventana.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()