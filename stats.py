#!/usr/bin/env python

from datetime import datetime
import re

import pytz
from tabulate import tabulate
import ovh

output = []
_print = print
def print(message):
    _print(message)
    output.append(message)


client = ovh.Client(config_file='./ovh.conf')

BILLING_ACCOUNT = 'ovhtel-17862213-1'
SERVICE_NAME = '0033478284789'

SERVICE = f'/telephony/{BILLING_ACCOUNT}/easyHunting/{SERVICE_NAME}'
QUEUE = SERVICE + '/hunting/queue/'
_queue = client.get(QUEUE)
if len(_queue) != 1:
    print("error, not one queue: " + repr(_queue))
    exit(1)

queueId = _queue[0]
queue = QUEUE + f'{queueId}'
stats = client.get(queue + '/liveStatistics')

print(datetime.fromtimestamp(client.get('/auth/time')).astimezone().isoformat())

print(tabulate( [ [ re.sub("([A-Z])"," \g<0>", key.lower().capitalize()), stats[key] ] for key in sorted(stats) ]))

calls = [ client.get(queue + f'/liveCalls/{id}') for id in sorted(client.get(queue + '/liveCalls')) ]
print(tabulate([ [ call['id'], call['callerIdNumber'].strip(), call['state'], call['agent'], call['begin'], call['answered'] ] for call in calls ],
               headers=['Id', 'CallerID', 'State', 'Agent', 'Begin', 'Answered']))


def save_log(message):
    tz = pytz.timezone('Europe/Paris')
    now = datetime.now(tz)
    filename = now.strftime("%Y-%m-%d.txt")
    with open(filename, "a") as file:
        file.write(message)
        
save_log("\n".join(output) + "\n")
