#!/usr/bin/env python

from datetime import datetime
import re
from tabulate import tabulate

import ovh

class SortedClient(ovh.Client):
    def dict_get(self, *args, **kwargs):
        return dict(sorted(self.get(*args, **kwargs).items()))
    def list_get(self, *args, **kwargs):
        return sorted(self.get(*args, **kwargs))

client = SortedClient(config_file='./ovh.conf')

BILLING_ACCOUNT = 'ovhtel-17862213-1'
SERVICE_NAME = '0033478284789'

SERVICE = f'/telephony/{BILLING_ACCOUNT}/easyHunting/{SERVICE_NAME}'
QUEUE = SERVICE + '/hunting/queue/'
AGENT = SERVICE + '/hunting/agent/'

_queue = client.list_get(QUEUE)
if len(_queue) != 1:
    print("error " + repr(_queue))
    exit(1)

queueId = _queue[0]
queue = QUEUE + f'{queueId}'
stats = client.dict_get(queue + '/liveStatistics')

print(datetime.fromtimestamp(client.get('/auth/time')).astimezone().isoformat())

print(tabulate( [ [ re.sub("([A-Z])"," \g<0>", key.lower().capitalize()), stats[key] ] for key in stats ]))

agents = [ client.get(AGENT + str(agent)) for agent in client.list_get(AGENT) ]
keys = agents[0].keys()
print(tabulate([[ agent[key] for key in keys ] for agent in agents ],
               headers=[re.sub("([A-Z])"," \g<0>", key).capitalize() for key in keys ]))


calls = [ client.dict_get(queue + f'/liveCalls/{id}') for id in client.list_get(queue + '/liveCalls') ]
print(tabulate([ [ call['id'], call['callerIdNumber'].strip(), call['state'], call['agent'], call['begin'], call['answered'] ] for call in calls ],
               headers=['Id', 'CallerID', 'State', 'Agent', 'Begin', 'Answered']))


