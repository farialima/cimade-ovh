#!/usr/bin/env python

#
# To run as a cron job, with a command like this (if running in PST timezone...):
# 0 4,7 * * * export PYTHONIOENCODING=utf8 && cd /this/directory && . /this/virtualenv/bin/activate && ./agents.py
#
#
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
    'Vendredi',
    'Samedi',
    'Dimanche',
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

def _print_agents():
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
        client.post(AGENT + f'{agent_id}/queue?queueId={queueId}',
                    position=0,
                    queueId=queueId)
        print(f'created as {agent_id} and enabled')

def _current_hour():
    tz = pytz.timezone('Europe/Paris')
    now = datetime.now(tz)
    if now.minute < 5:
        return now.hour
    if now.minute > 40:
        return now.hour + 1
  
    raise Exception(f'Should not run with local time: {now.hour}:{now.minute}')
    
def find_current_agent():
    day = DAYS_OF_WEEK[datetime.today().weekday()]

    hour = str(_current_hour()) + 'h'

    day_and_hour = day + ' ' + hour
    with open(FILE, encoding="utf-8") as userfile:
        for line in userfile:
            if line.lower().startswith(day_and_hour.lower()):
                break
        else:
            raise Exception(f'no line found for {day_and_hour} in {FILE}')
    print(f'Current info to set is: {line}')
    return _get_name_and_number(line)
   

def notify(message):
    msg = EmailMessage()
    msg.set_content(message)
    msg['From'] = "faria@john-adams.dreamhost.com"
    msg['To'] = "ovh-notification@farialima.net"
    msg['Subject'] = "Output put of OVH setting task"
    
    subprocess.run(["/usr/sbin/sendmail", "-t", "-oi"], input=msg.as_bytes())



def set_setting(**setting):
    ''' Set a setting for all agents. 

Valid settings are (from https://api.ovh.com/console/#/telephony/%7BbillingAccount%7D/easyHunting/%7BserviceName%7D/hunting/agent/%7BagentId%7D#PUT):

breakStatus       long
description       string
number            phoneNumber (not a good idea, though, to have the same number for all agents !!)
simultaneousLines long
status            telephony.OvhPabxHuntingAgentStatusEnum
timeout           long
wrapUpTime        long
 '''

    for agent in agents:
        print('Setting ' + str(setting) + ' for ' + agent['number'])
        client.put(AGENT + str(agent['agentId']), **setting)

def _get_name_and_number(line):
    # ugly but working :)
    line = line.replace('\n', '')
    day_and_hour = " ".join(line.split()[0:2])
    number = line.split()[-1]
    return line[len(day_and_hour)+1:-len(number)-1].replace(':', " ").replace("   ", " ").replace("  ", " ").strip(), number

def set_names():
    with open(FILE, encoding="utf-8") as userfile:
        for line in userfile:
            try:
                name, number = _get_name_and_number(line)
            except IndexError:
                print("Skipped line: " + repr(line))
                continue
            for agent in agents:
                if agent['number'] == number:
                    print('Setting name "' + name + '" for ' + number)
                    client.put(AGENT + str(agent['agentId']), description=name)
                    break
            else:
                print("agent not found for number: " + number)
            
    
#set_setting(wrapUpTime=10)
#set_names()

name, agent = find_current_agent()
set_agent(name, agent)


notify("\n".join(output))


