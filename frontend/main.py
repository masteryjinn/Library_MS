from PyQt6.QtWidgets import QApplication
from windows.auth.login import AuthWindow
import sys

def main():
    app = QApplication(sys.argv)
    window = AuthWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
#ddapp_oigLz5il9VSc7Mrtx0zSEEasr9WM4jkWpR
