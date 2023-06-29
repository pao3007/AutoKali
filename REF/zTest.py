import yaml

#otovríme config file
with open('a_ref_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

sample_rate = config['measurement']['sample_rate']
number_of_samples_per_channel = config['measurement']['number_of_samples_per_channel']

deviceName_channel = config['device']['name'] + '/' + config['device']['channel']

ref_name = config['save_data']['ref_name']
destination_folder = config['save_data']['destination_folder']

print(sample_rate, '\n')
print(number_of_samples_per_channel, '\n')
print(deviceName_channel, '\n')
print(ref_name, '\n')
print(destination_folder, '\n')

