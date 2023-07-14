import requests
import time
import os


class webapi:

    def __init__(self):
        self.interval = 1
        self.num_requests = 10

    def send_request(self):
        url = 'http://localhost:8024/api/v1/channels/1/last_data'  # Replace with your local API URL
        response = requests.get(url)
        if response.status_code == 200:
            self.json_data = response.json()
            # Process the JSON data here
        else:
            print('Error:', response.status_code)

    def start(self):
        for _ in range(self.num_requests):
            self.send_request()
            time.sleep(self.interval)
            print("NEW DATA")
            print(self.json_data)

    def start_sentinel(self):  # ! vybrat path to .exe a project

        sentinel_app = r'C:\Users\lukac\Desktop\Sylex\Sentinel\Sentinel2_Dynamic_v0_4_1 (AE)\Sentinel2_Dynamic_v0_4_1'
        sentinel_project = 'test.ssd'

        os.chdir(sentinel_app)
        os.system("start ClientApp_Dyn -api_autostart " + sentinel_project)


api = webapi()
api.start_sentinel()
# time.sleep(15)
# print("req start")
# api.start()
