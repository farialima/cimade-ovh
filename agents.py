#!/usr/bin/env python

from datetime import datetime
import re
import subprocess
from email.message import EmailMessage

import pytz
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

client = ovh.Client(config_file='./ovh.conf')

BILLING_ACCOUNT = 'ovhtel-17862213-1'
SERVICE_NAME = '0033478284789'

SERVICE = f'/telephony/{BILLING_ACCOUNT}/easyHunting/{SERVICE_NAME}'
QUEUE = SERVICE + '/hunting/queue/'
AGENT = SERVICE + '/hunting/agent/'

_queue = client.get(QUEUE)
if len(_queue) != 1:
    print("error, not one queue: " + repr(_queue))
    exit(1)

queueId = _queue[0]

output = []
_print = print
def print(message):
    _print(message)
    output.append(message)

agents = [ client.get(AGENT + str(agent)) for agent in sorted(client.get(AGENT)) ]

keys = sorted(agents[0].keys())
print(tabulate([[ agent[key] for key in keys ] for agent in agents ],
               headers=[re.sub("([A-Z])"," \g<0>", key).capitalize() for key in keys ]))

def set_agent(name, number):
    agent_id = None
    for agent in agents:
        if agent['number'] == number:
            agent_id = agent['agentId']
        elif agent['status'] != 'loggedOut':
            print('Disabling ' + agent['number'])
            client.put(AGENT + str(agent['agentId']), status='loggedOut')
    if agent_id:
        print('Enabling ' + number)
        client.put(AGENT + str(agent_id), status='available')
    else:
        print(f'Agent for name "{name}" and number {number} not found, creating and enabling it...')
        result = client.post(AGENT,
                             description=name,
                             number=number,
                             simultaneousLines=1,
                             status='available',
                             timeout=10,
                             wrapUpTime=0
        )
        agent_id = result['agentId']
        client.post(AGENT + f'{agent_id}/queue',
                    position=0,
                    queueId=queueId)
        print(f'created as {agent_id} and enabled')



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
    return line[len(day_and_hour)+1:-len(line.split()[-1])-1].replace(':', " ").replace("   ", " ").replace("  ", " ").strip(), line.split()[-1]
    

name, agent = find_current_agent()
set_agent(name, agent)

def notify(message):
    msg = EmailMessage()
    msg.set_content(message)
    msg['From'] = "faria@john-adams.dreamhost.com"
    msg['To'] = "ovh-notification@farialima.net"
    msg['Subject'] = "Output put of OVH setting task"
    
    subprocess.run(["/usr/sbin/sendmail", "-t", "-oi"], input=msg.as_bytes())


notify("\n".join(output))
