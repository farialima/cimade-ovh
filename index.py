#!/usr/bin/python3

this_file='/home/faria/permtel.farialima.net/.venv3/bin/activate_this.py'

exec(open(this_file).read(), dict(__file__=this_file))

import os
import sys
from urllib.parse import parse_qs
import html
import re
from datetime import datetime
import subprocess
from email.message import EmailMessage
from html import escape


import pytz
import ovh


APPLICATION_ID=126066
class Client(ovh.Client):
    def __init__(self):
        super(Client, self).__init__(config_file='./ovh.conf')
        self.check_credentials()
        
    def check_credentials(self):
        # this is not really needed since we use unlimited token... but I wrote it so I leave it :)
        max_expiration_dates = max(
            # if no expiration date, it's unlimited
            datetime.strptime((self.get('/me/api/credential/'+str(id))['expiration'] or '2999-12-31T00:00').split('T')[0],
                                  '%Y-%m-%d').date()
            for id in self.get('/me/api/credential', applicationId=APPLICATION_ID))
        remaining = (max_expiration_dates - datetime.now().date()).days
        if (remaining < 7):
            notify(f"Les credentials vont expirer dans {remaining} jours !!!")
        if (remaining < 2): 
            print_html(f'''<p style="color: red">Attention: les permissions d'acc&egrave;s &agrave; pour cette page vont expirer dans {remaining} jour(s) - ensuite cette page ne fonctionnera plus !<br/>
Contactez François au 06 99 12 47 55 ou <a href="mailto:francois@granade.com">francois@granade.com</a> pour qu'il les renouvelle</p>
''')

        
class Redirect(Client):
    def __init__(self, billing_account, service_name, sip):
        super(Redirect, self).__init__()
        self.sip = f'/telephony/{billing_account}/line/{sip}/options'
        # some verifications
        redirect_info = self.get(f'/telephony/{billing_account}/redirect/{service_name}')
        if ("destination" not in redirect_info
            or 'featureType' not in redirect_info
            or redirect_info['featureType'] != 'redirect'):
              raise Exception(f'Line {service_name} not configured for redirection')
        if redirect_info['destination'] != sip:
              raise Exception(f'Line {service_name} is redirected to {redirect_info["destination"]} instead of {sip}')

    def calls(self):
        return None, None
    
    def set_agent(self, number):
        self.put(self.sip,
                       forwardUnconditional=True,
                       forwardUnconditionalNumber=number)
    def start_perm(self):
        # nothing to do -- all in set_agent
        pass
    
    def stop_perm(self):
        self.delete_all_agents()
        
    def is_started(self):
        return self.get_active_agent() != None
    
    def get_active_agent(self):
        agent = self.get(self.sip)
        if agent['forwardUnconditional']:
            return agent['forwardUnconditionalNumber']
        
    def delete_all_agents(self):
        # there's only one agent...
        self.put(self.sip,
                       forwardUnconditional=False)
        
class Queue(Client):
    def __init__(self, billing_account, service_name):
        super(Queue, self).__init__()
        self.service = f'/telephony/{billing_account}/easyHunting/{service_name}'
        self.queue_name = self.service + '/hunting/queue/'
        self.agent = self.service + '/hunting/agent/'
        self.conditions = self.service + '/timeConditions/conditions'
        queues = self.get(self.queue_name)
        if len(queues) != 1:
            raise Exception("error, not one queue: " + repr(queues))
        self.queueId = queues[0]

    def calls(self):
        queue = self.queue_name + f'{self.queueId}'
        calls = [ self.get(queue + f'/liveCalls/{id}') for id in sorted(self.get(queue + '/liveCalls')) ]
        waiting_calls = [ call for call in calls if call['state'] == 'Waiting' ]
        answered_calls = [ call for call in calls if  call['state'] == 'Answered' ]
        return waiting_calls, answered_calls
    
    def start_perm(self):
        tz = pytz.timezone('Europe/Paris')
        day = WEEKDAYS[datetime.now(tz).weekday()].lower()
        try:
            self.post(self.conditions,
                        timeFrom="02:00:00",
                        timeTo="23:59:59",
                        weekDay=day,
                        policy="available")
        except ovh.exceptions.BadParametersError as e:
            print(e)

    def stop_perm(self):
        try:
            condition = self._condition()
            if not condition:
                raise Exception("Perm not started")
            # {'timeFrom': '19:00:00', 'policy': 'available', 'timeTo': '23:59:59', 'weekDay': 'sunday', 'conditionId': 2692226}
            conditionId = condition['conditionId']

            #print(f'Deleting: {conditionId}')
            self.delete(self.conditions + f'/{conditionId}')
        except ovh.exceptions.BadParametersError as e:
            print(e)

    def is_started(self):
        return self._condition() != None
    
    def _condition(self):
        conditions = self.get(self.conditions)
        for conditionId in conditions:
            condition_details = self.get(self.conditions + f'/{conditionId}')
            if condition_details['timeTo'] == '23:59:59':
                return condition_details

    def _agents(self):
        return [ self.get(self.agent + str(agent)) for agent in sorted(self.get(self.agent)) ]
    
    def get_active_agent(self):
        for agent in self._agents():
            if agent['status'] != 'loggedOut':
                return agent['number']

    def set_agent(self, number):
        agent_id = None
        for agent in self._agents():
            if agent['number'] == number:
                agent_id = agent['agentId']
            elif agent['status'] != 'loggedOut':
                #print('Disabling ' + agent['number'])
                self.put(self.agent + str(agent['agentId']), status='loggedOut')
        if agent_id:
            #print('Enabling ' + number)
            self.put(self.agent + str(agent_id), status='available')
        else:
            #print(f'Agent for number {number} not found, creating and enabling it...')
            result = self.post(self.agent,
                                 description='(no known name)',
                                 number=number,
                                 simultaneousLines=1,
                                 status='available',
                                 timeout=10,
                                 wrapUpTime=0
            )
            agent_id = result['agentId']
            self.post(self.agent + f'{agent_id}/queue?queueId={self.queueId}',
                        position=0,
                        queueId=self.queueId)
            #print(f'created as {agent_id} and enabled')

    def delete_all_agents(self):
        conditions = self.get(self.conditions)
        for conditionId in conditions:
            condition_details = self.delete(self.conditions + f'/{conditionId}')
            print(condition_details)

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

def french_datetime():
    import locale
    current_locale = locale.getlocale()[0]
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR")
        tz = pytz.timezone('Europe/Paris')
        now = datetime.now(tz)
        return now.strftime("%A %d %b %Y à %H:%M:%S")
    finally:
        locale.setlocale(locale.LC_TIME, current_locale)
    
def format_tel(tel):
    number = tel.replace(' ', '').replace('-', '')
    if not isascii(number) or not number.isnumeric():
        raise Exception("Le numéro de téléphone doit n'avoir que des chiffres : " + repr(tel)) 
    if len(number) != 10:
        raise Exception("Le numéro de téléphone doit avoir 10 chiffres, reçu : " + "".join([repr(c).replace("'", '') for c in number]))
    if not number.startswith("0"):
        raise Exception("Le numéro de téléphone doit commencer par un zero")
    
    return "0033" + number[1:]

_french_call = lambda caller: re.sub('^0033', '0', re.sub('^33', '0', caller.strip()))

def print_html(message):
    print(message.encode('ascii', 'xmlcharrefreplace').decode('ascii'))


CITY = os.environ['REQUEST_URI'].replace('/', '').capitalize() or 'Undefined'
    
def notify(message):
    msg = EmailMessage()
    msg.set_content(message + "\n\nSee https://permtel.farialima.net/ for more information.")
    msg['From'] = "faria@john-adams.dreamhost.com"
    msg['To'] = "ovh-notification@farialima.net"
    msg['Subject'] = f"Permtel notification pour {CITY}"
    
    subprocess.run(["/usr/sbin/sendmail", "-t", "-oi"], input=msg.as_bytes())


def do_page():

    print("Content-type: text/html\n\n")

    print_html(f'''<html>
<body>
''')
    try:
        if CITY == "Lyon":
            TEL='0033478284789'
            line = Queue('ovhtel-17862213-1', TEL)
        elif CITY == "Lille":
            TEL='0033320543514'
            line = Redirect('ovhtel-15669832-1', TEL, '0033972366112')
        else:
            print(f'<html><body>Pas de ville s&eacute;lectionn&eacute;, retournez sur la <a href="/">page de s&eacute;lection</a></body></html>')
            notify('Pas de ville pour ' + str(os.environ['REQUEST_URI']))
            return
    except Exception as e:
        notify(str(e))
        print(e)
        raise

    tel = ''
    now = french_datetime()
    print_html(f'''<h1>Permanences T&eacute;l&eacute;phoniques Cimade {CITY}</h1>
<p><b>Cette page est pour {CITY} sur le num&eacute;ro {_french_call(TEL)}.</b><br/>
<i>Pour la liste des villes, allez <a href="/">ici</a></i></p>
<p><i>Page actualisée le {now}. <a href="./">Actualiser cette page</a></i></p>
''')
    

    if ('REQUEST_METHOD' in os.environ and os.environ['REQUEST_METHOD'] == 'POST'):
        query_string = sys.stdin.read()
        multiform = parse_qs(query_string)
        # or:
        #import cgi
        #form = cgi.FieldStorage()
        try:
            if 'finish' in multiform:
                line.stop_perm()
                print_html(f'<p style="color: blue">Permanence terminée</p>')
                notify('Permanence terminée')
            else:
                 # unescape needed because when copy/pasting on Safari, getting chars like "&#8236;" !!
                tel = html.unescape(multiform['tel'][0]) if 'tel' in multiform else ''
                number = format_tel(tel)
                line.set_agent(number)
                line.start_perm()
                print_html(f'<p style="color: blue">Permanence commencée sur le numéro {tel}</p>')
                notify(f'Permanence commencée sur le numéro {tel}')
           
        except Exception as e:
            print_html(f'''<p style="color: red">Erreur: {e}</p>
<p>Si probl&egrave;me, contactez François au 06 99 12 47 55</p>
<p><i><a href="./">Actualiser cette page</a></i></p>
''')
            notify(f'error when setting permanence: {e}')

    print('''<h2>&Eacute;tat actuel</h2>''')
    
    is_started = line.is_started()
    print_html("<b>Permanence en cours :</b>")
    if not is_started:
        print_html("Pas de permanence en cours<br/>")
    else:
        print_html(" répondue par&nbsp;: ")
        agent = line.get_active_agent()
        if not agent:
            print_html("(pas de num&eacute;ro de réponse))")
        else:
            print_html(_french_call(agent))
    print_html("<br/><br/>")

    waiting_calls, answered_calls = line.calls()
    _time = lambda date: ' à ' + date[11:16]
    if answered_calls != None:
        print_html("<b>Appel en cours :&nbsp;</b>")
        if answered_calls:
            for call in answered_calls:
                print_html("<br/>du " + _french_call(call['callerIdNumber']) + _time(call['begin'])
                            + ", repondu par " + _french_call(call['agent']) + _time(call['answered']))
        else:
            print("Pas d'appel")
        print("<br/><br/>")
    if waiting_calls == None:
        print("<b><i>Pas de file d'attente d'appels</i></b>\n")        
    else:
        print("<b>Appels en attente :</b>\n")
        if waiting_calls:
            for call in waiting_calls:
                print(" <br/>\n")
                print_html("du " + _french_call(call['callerIdNumber']) + _time(call['begin']))
        else:
            print("Pas d'appels")

    if is_started:
        print_html('<h2>Changer de num&eacute;ro</h2>')
    else:
        print_html('<h2>D&eacute;marrer la permanence</h2>')
        
    print_html(f'''
<form action="." method="POST"> 
Votre num&eacute;ro de t&eacute;l&eacute;phone (10 chiffres)&nbsp;:&nbsp;<input name="tel" value="{tel}"/><br/>
<input type="submit" value="R&eacute;pondre sur ce num&eacute;ro"/>
</form>
''')

    if is_started:
        print_html(f'''
<h2>Terminer la permanence</h2>
<form action="." method="POST"> 
<input type="hidden" name="finish" value="yes"/>
Si vous avez fini, cliquez&nbsp;:&nbsp;<input type="submit" value="Terminer la permanence"/>
''')
        if answered_calls != None:
            print_html(f'''
<p style="color:red">Attention, une fois la permanence terminée, vous recevrez encore les appels en attente.</p>
''')
        print_html(f'''
</form>
''')
    print_html('''
</body>
</html>
''')

do_page()
        
#client.delete_all_agents()
