import os
import json
import psutil
import ibmiotf.application
import uuid
import sys
import time

messages_send = 0


# Env Setup
if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    print('This means cloud foundry')
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        print('This means dev env.')
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

# Util functions
# Get current Memory usage
def getMemoryUsage():
    process = psutil.Process(os.getpid())
    return "Memory usage: {}MB".format(process.memory_info().rss/1000000)

# Callback message
class CallBackHelper():
    def __init__(self):
        self.messages_send = 0

    def publishCallback(self):
        self.messages_send += 1

######### Application #########
qos_levels = [0, 1, 2];
sending_times = [10, 100, 1000, 10000, 100000];
device_type = "SimDevice"
device_id = "SimDevice"

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
            print("Iteration: {}_{}_{}".format(sending_time,actual_size,qos))
            print("Starting to send messages")
            mycallbackhelper = CallBackHelper()
            for i in range(0,sending_time):
                send_success = 0
                while(not send_success):
                    send_success = appClient.publishEvent(device_type, device_id, "calculator-event", "json", jsonconf['sizes'][jsoninput], qos=qos,on_publish=mycallbackhelper.publishCallback)
                    #print("sending_time: {} - messages_send: {}".format(i, messages_send))
                    if not send_success:
                        print("send_success is false. Trying again")
            print("Finished queuing messages")
            while(sending_time != mycallbackhelper.messages_send):
                #print("sending_time: {} - messages_send: {}".format(sending_time, messages_send))
                pass
            #print("sending_time: {} - messages_send: {}".format(sending_time, messages_send))
            time_took = round(time.time()-t0, 3)-(10*times_interrupted)
            print("Finished sending messages")
            print("Took {} seconds".format(time_took))
            time.sleep(1)
            print(getMemoryUsage())
