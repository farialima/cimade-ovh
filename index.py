#!/usr/bin/python3

this_file='/home/faria/permtel.farialima.net/.venv3/bin/activate_this.py'

exec(open(this_file).read(), dict(__file__=this_file))

import os
import sys
from urllib.parse import parse_qs
import html
import re
from datetime import datetime
from email.message import EmailMessage
from html import escape


import pytz
import ovh

client = ovh.Client(config_file='./ovh.conf')

BILLING_ACCOUNT = 'ovhtel-17862213-1'
SERVICE_NAME = '0033478284789'

SERVICE = f'/telephony/{BILLING_ACCOUNT}/easyHunting/{SERVICE_NAME}'
QUEUE = SERVICE + '/hunting/queue/'
AGENT = SERVICE + '/hunting/agent/'
CONDITIONS = SERVICE + '/timeConditions/conditions'

_queue = client.get(QUEUE)
if len(_queue) != 1:
    print("error, not one queue: " + repr(_queue))
    exit(1)

queueId = _queue[0]

WEEKDAYS = [
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday',
    ]


try:
    # python >= 3.7
    isascii = str.isascii
except:
    def isascii(string):
        try:
            string.encode('ascii')
        except UnicodeEncodeError:
            return False
        return True
    
def format_tel(tel):
    number = tel.replace(' ', '').replace('-', '')
    if len(number) != 10:
        raise Exception("Le numero de telephone doit avoir 10 chiffres, reçu : " + "".join([repr(c).replace("'", '') for c in number]))
    if not isascii(number) or not number.isnumeric():
        raise Exception("Le numero de telephone doit n'avoir que des chiffres : " + repr(tel)) 
    if not number.startswith("0"):
        raise Exception("Le numero de telephone doit commencer par un zero")
    
    return "0033" + number[1:]

_french_call = lambda caller: re.sub('^0033', '0', re.sub('^33', '0', caller.strip()))

def start_perm():
    tz = pytz.timezone('Europe/Paris')
    day = WEEKDAYS[datetime.now(tz).weekday()].lower()
    try:
        client.post(CONDITIONS,
                    timeFrom="02:00:00",
                    timeTo="23:59:59",
                    weekDay=day,
                    policy="available")
    except ovh.exceptions.BadParametersError as e:
        print(e)

def get_condition():
    conditions = client.get(CONDITIONS)
    for conditionId in conditions:
        condition_details = client.get(CONDITIONS + f'/{conditionId}')
        if condition_details['timeTo'] == '23:59:59':
            return condition_details

def get_active_agent():
    agents = [ client.get(AGENT + str(agent)) for agent in sorted(client.get(AGENT)) ]
    for agent in agents:
        if agent['status'] != 'loggedOut':
            return agent

def set_agent(number):
    agent_id = None
    agents = [ client.get(AGENT + str(agent)) for agent in sorted(client.get(AGENT)) ]
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
        print(f'Agent for number {number} not found, creating and enabling it...')
        result = client.post(AGENT,
                             description='(no known name)',
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

        
def stop_perm():
    try:
        condition = get_condition()
        if not condition:
            raise Exception("Current condition not found")
        # {'timeFrom': '19:00:00', 'policy': 'available', 'timeTo': '23:59:59', 'weekDay': 'sunday', 'conditionId': 2692226}
        conditionId = condition['conditionId']

        print(f'Deleting: {conditionId}')
        client.delete(CONDITIONS + f'/{conditionId}')
    except ovh.exceptions.BadParametersError as e:
        print(e)

def do_page():

    print("Content-type: text/html\n\n")

    def print_html(message):
        print(message.encode('ascii', 'xmlcharrefreplace').decode('ascii'))

    tel = ''
    print_html('''<html>
<body>
<h1>Permanences T&eacute;l&eacute;phoniques Cimade Lyon</h1>
<p><button onClick="window.location.reload();">Actualiser cette page</button></p>
''')

    if ('REQUEST_METHOD' in os.environ and os.environ['REQUEST_METHOD'] == 'POST'):
        query_string = sys.stdin.read()
        multiform = parse_qs(query_string)
        try:
            if 'tel' in multiform:
                tel = html.unescape(multiform['tel'][0]) # unescape needed because when copy/pasting on Safari, getting chars like "&#8236;" !!
                number = format_tel(tel)
                set_agent(number)
                start_perm()
                print_html(f'<p style="color: blue">Permanence commencée sur le numéro {tel}</p>')
            else:
                stop_perm()
                print_html(f'<p style="color: blue">Permanence terminée</p>')
        except Exception as e:
            print_html(f'<p style="color: red">Erreur: {e}</p>')
            print_html('Si probleme, Contactez François au 06 99 12 47 55')
            raise

    print('''<h2>&Eacute;tat actuel</h2>''')
    
    condition = get_condition()
    print_html("<b>Permanence en cours :</b>")
    if not condition:
        print_html("Pas de permanence en cours<br/>")
    else:
        print_html(" répondue par&nbsp;: ")
        agent = get_active_agent()
        if not agent:
            print_html("(pas de numero de réponse))")
        else:
            print_html(_french_call(agent['number']))
    print_html("<br/><br/>")
                           
    queue = QUEUE + f'{queueId}'
    calls = [ client.get(queue + f'/liveCalls/{id}') for id in sorted(client.get(queue + '/liveCalls')) ]
    waiting_calls = [ call for call in calls if call['state'] == 'Waiting' ]
    answered_calls = [ call for call in calls if  call['state'] == 'Answered' ]

    _time = lambda date: ' à ' + date[11:16]
    print_html("<b>Appel en cours :&nbsp;</b>")
    if answered_calls:
        call = answered_calls[0]
        print_html("<br/>du " + _french_call(call['callerIdNumber']) + _time(call['begin'])
                       + ", repondu par " + _french_call(call['agent']) + _time(call['answered']))
    else:
        print("Pas d'appel")
    print("<br/><br/>")
    print("<b>Appels en attente :</b>\n")
    if waiting_calls:
        for call in waiting_calls:
            print(" <br/>\n")
            print_html("du " + _french_call(call['callerIdNumber']) + _time(call['begin']))
    else:
        print("Pas d'appels")
    
    print_html(f'''<h2>D&eacute;marrer la permanence ou changer de numero </h2>

<form action="index.py" method="POST"> 

Votre num&eacute;ro de t&eacute;l&eacute;phone (10 chiffres)&nbsp;:&nbsp;<input name="tel" value="{tel}"/><br/>
<input type="submit" value="R&eacute;pondre sur ce num&eacute;ro"/>

<h2>Terminer la permanence</h2>
Si vous avez fini, cliquez&nbsp;:&nbsp;<input type="submit" value="Terminer la permanence"/>
<br/>
Attention, une fois la permanence terminée, vous recevrez encore les appels en attente.
</form>
''')
    print_html('''</body>
</html>
''')

do_page()
def delete_conditions():
    conditions = client.get(CONDITIONS)
    for conditionId in conditions:
        condition_details = client.delete(CONDITIONS + f'/{conditionId}')
        print(condition_details)
        
#delete_conditions()
