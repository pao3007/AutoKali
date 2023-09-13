import pyvisa

rm = pyvisa.ResourceManager()
resources = rm.list_resources()
for resource_name in resources:

    # instrument = rm.open_resource(resource_name)
    # instrument.close()
    print(resource_name)
