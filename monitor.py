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

billingAccount = 'ovhtel-17862213-1'
serviceName = '0033478284789'

service = f'/telephony/{billingAccount}/easyHunting/{serviceName}'

#print(client.get(service))

_queue = client.list_get(service + '/hunting/queue')
if len(_queue) != 1:
    print("error " + repr(_queue))
    exit(1)

queueId = _queue[0]
queue = service + f'/hunting/queue/{queueId}'
stats = client.dict_get(queue + '/liveStatistics')

print(tabulate( [ [ re.sub("([A-Z])"," \g<0>", key.lower().capitalize()), stats[key] ] for key in stats ]))

calls = [ client.dict_get(queue + f'/liveCalls/{id}') for id in client.list_get(queue + '/liveCalls') ]
print(tabulate([ [ call['id'], call['callerIdNumber'].strip(), call['state'], call['agent'], call['begin'], call['answered'] ] for call in calls ],
               headers=['Id", CallerID', 'State', 'Agent', 'Begin', 'Answered']))


print(datetime.fromtimestamp(client.get('/auth/time')).astimezone().isoformat())