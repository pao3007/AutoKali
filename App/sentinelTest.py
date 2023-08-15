import os

sentinel_app = r'C:\Users\lukac\Desktop\Sylex\Sentinel\Sentinel2_Dynamic_v0_4_1 (AE)\Sentinel2_Dynamic_v0_4_1'
sentinel_project = 'test.ssd'

os.chdir(sentinel_app)
os.system("start ClientApp_Dyn -"
          "autolog=NO -api_autostart " + sentinel_project)