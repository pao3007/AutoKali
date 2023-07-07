import subprocess


def start_app_with_arguments(app_path):
    subprocess.run([app_path])


# Example usage
app_path = 'C:/Users/lukac/Desktop/Sylex/Sentinel/Sentinel2_v1_0_44/Sentinel2_v1_0_44/ClientApp/ClientApp.exe'

start_app_with_arguments(app_path)

# def start_app_with_arguments(app_path, arguments):
#     subprocess.Popen([app_path] + arguments)
#
#
# # Example usage
# app_path = r'C:\Users\lukac\Desktop\Sylex\Sentinel\Sentinel2_v1_0_44\Sentinel2_v1_0_44\ClientApp\ClientApp.exe'
# project_file = 'path/to/your/saved_project.ssd'
# additional_argument = '-argument'
# start_app_with_arguments(app_path, [additional_argument, project_file])
