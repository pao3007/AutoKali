from PyQt5.QtWidgets import QApplication, QTextBrowser
from PyQt5.QtCore import Qt

app = QApplication([])

text_browser = QTextBrowser()

left_text = "This is aligned to the left."
right_text = "This is aligned to the right."
line2 = "This is aligned to the center."

html = f"<table width='100%'><tr><td align='left'>{left_text}</td><td align='right'>{right_text}</td></tr></table>"
html += f"<div style='text-align: center;'>{line2}</div>"

text_browser.setHtml(html)

text_browser.show()

app.exec_()
