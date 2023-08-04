import chardet
file_path = r"C:/Users/lukac/Desktop/Sylex/QTDesigner/Appka/content/Screen01.ui.qml"

with open(file_path, 'rb') as file:
    data = file.read()
    result = chardet.detect(data)
    file_encoding = result['encoding']

print("Detected file encoding:", file_encoding)
