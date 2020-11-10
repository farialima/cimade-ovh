#!/usr/bin/env python

from datetime import datetime
import pytz
import re
from tabulate import tabulate

import ovh

FILE = 'users.txt'
DAYS_OF_WEEK = [
    'Lundi',
    'Mardi',
    'Mercredi',
    'Jeudi',
    'Vendredi'
    'Samedi',
    'Dimanche'
    ]

BILLING_ACCOUNT = 'ovhtel-17862213-1'
SERVICE_NAME = '0033478284789'

SERVICE = f'/telephony/{BILLING_ACCOUNT}/easyHunting/{SERVICE_NAME}'
AGENT = SERVICE + '/hunting/agent/'

class SortedClient(ovh.Client):
    def dict_get(self, *args, **kwargs):
        return dict(sorted(self.get(*args, **kwargs).items()))
    def list_get(self, *args, **kwargs):
        return sorted(self.get(*args, **kwargs))

client = SortedClient(config_file='./ovh.conf')

agents = [ client.get(AGENT + str(agent)) for agent in client.list_get(AGENT) ]

keys = agents[0].keys()
print(tabulate([[ agent[key] for key in keys ] for agent in agents ],
               headers=[re.sub("([A-Z])"," \g<0>", key).capitalize() for key in keys ]))

def set_agent(number):
    agent_id = None
    for agent in agents:
        if agent['number'] == number:
            agent_id = agent['agentId']
        elif agent['status'] != 'loggedOut':
            print('Disabling ' + agent['number'])
            client.put(AGENT + str(agent['agentId']), status='loggedOut')
    if not agent_id:
        print(f'Agent for number {number} not found')
        exit(-1)

    print('Enabling ' + number)
    client.put(AGENT + str(agent_id), status='available')


def find_current_agent():
    day = DAYS_OF_WEEK[datetime.today().weekday()]

    tz = pytz.timezone('Europe/Paris')
    now = datetime.now(tz)
    if now.hour in [15, 16]:
        hour = '4PM'
    elif now.hour in [12, 13, 14]:
        hour = '2PM'
    else:
        raise Exception(f'Should not run with local time: {now.hour}')

    day_and_hour = day + ' ' + hour
    with open(FILE) as userfile:
        for line in userfile:
            if line.startswith(day_and_hour):
                break
        else:
            raise(f'no line found for {day_and_hour} in {FILE}')
    print(f'Current info to set is: {line}')
    return line.split()[-1]
    

agent = find_current_agent()
set_agent(agent)