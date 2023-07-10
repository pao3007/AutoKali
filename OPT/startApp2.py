import os
import time

sentinel_app = r'C:\Users\lukac\Desktop\Sylex\Sentinel\Sentinel2_Dynamic_v0_4_1 (AE)\Sentinel2_Dynamic_v0_4_1'
sentinel_project = 'test.ssd'

os.chdir(sentinel_app)
os.system("start ClientApp_Dyn " + sentinel_project)

app_name = "ClientApp_Dyn"



print("test")
time.sleep(15)
print("zatvaram")
# os.system(f'taskkill /F /IM {app_name}.exe')
