import os
import json
import psutil
import ibmiotf.application
import uuid
import time

# Env Setup
if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    print('This means cloud foundry. Setting wait_time to 10800')
    wait_time = 10800
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        print('This means dev env. Setting wait_time to 1')
else:
    sys.exit("No vcap found")

# Log version (git commit hash)
if os.path.isfile('VERSION'):
    with open('VERSION') as f:
        version = f.readline()
        date = f.readline()
        print("Running git commit: {}This was last verified: {}".format(version,date))
else:
    print("Could not find VERSION file")

# Load input jsons
if os.path.isfile('jsonconf.json'):
    with open('jsonconf.json') as f:
        jsonconf = json.load(f)

#Setup ibmiotf
if not 'iotf-service' in vcap:
    sys.exit("No iotf-service in VCAP_SERVICES")
    
appClientConfig = {
    "org": vcap['iotf-service'][0]['credentials']['org'],
    "id": str(uuid.uuid4()),
    "auth-method": "apikey",
    "auth-key": vcap['iotf-service'][0]['credentials']['apiKey'],
    "auth-token": vcap['iotf-service'][0]['credentials']['apiToken'],
  }
appClient = ibmiotf.application.Client(appClientConfig)
appClient.connect()

######### Application #########
qos_levels = [0, 1, 2];
sending_times = [10, 100, 1000, 10000, 100000];

print(getMemoryUsage())
print("Input File contains {} JSON Objects".format(len(jsonconf['sizes'])))
for sending_time in sending_times:
    print("Sending messages {} times.".format(sending_time))
    for jsoninput in jsonconf['sizes']:
        print("JSON input size is: {}".format(jsoninput))
        actual_size = len(json.dumps(jsonconf['sizes'][jsoninput]).encode('utf-8'))
        print("Calculated size is: {}".format(actual_size))
        for qos in qos_levels:
            print("Messages with QoS: {}".format(qos))
            t0 = time.time()
            times_interrupted = 0
            print("Starting to send messages")
            for i in range(0,sending_time):
                appClient.publishEvent(device_type, device_id, "calculator-event", "json", jsonconf['sizes'][jsoninput], qos=qos)
            time_took = round(time.time()-t0, 3)-(10*times_interrupted)
            print("Finished sending messages")
            print("Took {} seconds".format(time_took))
            time.sleep(1)
            print(getMemoryUsage())

# Get current Memory usage
def getMemoryUsage():
    process = psutil.Process(os.getpid())
    return "Memory usage: {}MB".format(process.memory_info().rss/1000000)
