import subprocess

# Specify the path to the application executable

app_path = [r'C:\Users\lukac\Desktop\Sylex\Sentinel\Sentinel2_Dynamic_v0_4_1 (AE)\Sentinel2_Dynamic_v0_4_1\ClientApp_Dyn.exe']
sentinel_project = 'test.ssd'

# Launch the application in the background without showing a window
process = subprocess.Popen(app_path)  # , creationflags=subprocess.CREATE_NO_WINDOW
process.wait()

if process.returncode == 0:
    print('Application started successfully.')
else:
    print('Failed to start the application.')

error_output = process.stderr.read()

# Decode and print the error messages
print(error_output.decode())