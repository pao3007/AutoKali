import os
import time

app_path = r'C:\Users\lukac\Desktop\Sylex\Sentinel\Sentinel2_Dynamic_v0_4_1 (AE)\Sentinel2_Dynamic_v0_4_1'

os.chdir(app_path)
os.system("start ClientApp_Dyn test.ssd")

app_name = "ClientApp_Dyn"
print("test")
time.sleep(15)
print("zatvaram")
# os.system(f'taskkill /F /IM {app_name}.exe')
