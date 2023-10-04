from PyQt5.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu, QAction
import sys

def menu_item_triggered():
    print("Menu item clicked!")

app = QApplication([])

window = QMainWindow()

menu_bar = QMenuBar()
file_menu = QMenu("File", menu_bar)
menu_item = QAction("Do Something", file_menu)

menu_item.triggered.connect(menu_item_triggered)

file_menu.addAction(menu_item)
menu_bar.addMenu(file_menu)

window.setMenuBar(menu_bar)
window.show()

sys.exit(app.exec_())
