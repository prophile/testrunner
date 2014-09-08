from irc.bot import *
import redis
import threading
import hammock
import json
import uuid
import urllib.parse
import urllib.request
import re

IRC_NETWORK="irc.freenode.net"
IRC_PORT=6667
IRC_CHANNEL="#srobo-test"
IRC_NICK="sr-cibot"
GERRIT_ROOT="https://www.studentrobotics.org/gerrit"
PROJECT_ROOT="{}/p/".format(GERRIT_ROOT)

def paste(content):
    form = {'paste[parser]': 'plain_text',
            'paste[body]': content,
            'paste[authorization]': 'burger',
            'paste[restricted]': '0'}
    f = urllib.request.urlopen('http://pastie.org/pastes',
                               urllib.parse.urlencode(form).encode('utf-8'))
    f.close()
    return f.geturl()


class MainBot(SingleServerIRCBot):
    def __init__(self):
        super().__init__([ServerSpec(IRC_NETWORK, IRC_PORT)],
                         IRC_NICK, IRC_NICK)
        self.send = lambda msg: None
        self.receive = lambda sender, msg: None

    def on_welcome(self, conn, event):
        conn.join(IRC_CHANNEL)

    def on_pubmsg(self, conn, event):
        self.send = lambda x: conn.privmsg(IRC_CHANNEL, x)
        print(event.source)
        match = re.match('^(.+)!(.+)@(.+)$', event.source)
        if match is None:
            self.send('What, who said that?')
        print(event.arguments[0])
        self.receive(match.group(1), event.arguments[0])

def main():
    gerrit = hammock.Hammock(GERRIT_ROOT)

    def get_json(path):
        return json.loads(path.GET().text[5:])

    bot = MainBot()

    def send(msg):
        bot.send(msg)
    conn = redis.StrictRedis()

    listeners = {}

    def redis_subscribe():
        sub = conn.pubsub(ignore_subscribe_messages=True)
        sub.subscribe('jobs')
        for message in sub.listen():
            jobID, state = message['data'].decode('utf-8').split(' ')
            listener = listeners.get(jobID)
            if listener is not None:
                del listeners[jobID]
                (recipient, what) = listener
                if state == 'complete':
                    send('{}: Your build of {} passed.'.format(recipient, what))
                else:
                    logs = conn.get('jobs:{}:log'.format(jobID))
                    pasted = paste(logs)
                    send('{}: Your build of {} failed. Logs: {}'.format(recipient, what, pasted))
                    # TODO: paste failure somewhere
    thread_redis = threading.Thread(name='Sub', target=redis_subscribe)
    thread_redis.daemon = True
    thread_redis.start()

    def submit_job(sender, uri, ref, desc):
        jobID = str(uuid.uuid4())
        conn.rpush('queue:builds', '{} {} {}'.format(uri, ref, jobID))
        send('{}: OK, I\'ll let you know when the build on {} is finished.'.format(sender, desc))
        listeners[jobID] = (sender, desc)

    def handle_message(sender, msg):
        prefix = '{}:'.format(IRC_NICK)
        if not msg.startswith(prefix):
            return
        msg = msg[len(prefix):].strip()
        if msg == 'help':
            send('Usage:')
            send('  {}: build g:[gerrit change]'.format(IRC_NICK))
            send('  {}: build [project].git'.format(IRC_NICK))
            send('  {}: build [project].git [branch]'.format(IRC_NICK))
            return
        match = re.match('build\s+g:(\d+)$', msg)
        if match is not None:
            # Gerrit build
            change = int(match.group(1))
            try:
                data = get_json(gerrit.changes(change).detail)
                revision = max(msg['_revision_number'] for msg in data['messages'])
                proj = data['project']
                uri = urllib.parse.urljoin(PROJECT_ROOT, proj)
                ref = "refs/changes/{}/{}/{}".format(str(change)[-2:], change, revision)
                submit_job(sender, uri, ref, 'g:{} ({})'.format(change, proj))
            except ValueError:
                send('{}: I couldn\'t get that change from Gerrit.'.format(sender))
            return
        match = re.match(r'build\s+(\S+)\.git$', msg)
        if match is not None:
            uri = urllib.parse.urljoin(PROJECT_ROOT, match.group(1))
            ref = "refs/heads/master"
            submit_job(sender, uri, ref, match.group(1) + '.git')
            return
        match = re.match(r'build\s+(\S+)\.git\s+(\S+)$', msg)
        if match is not None:
            proj = match.group(1)
            branch = match.group(2)
            uri = urllib.parse.urljoin(PROJECT_ROOT, proj)
            ref = "refs/heads/" + branch
            submit_job(sender, uri, ref, '{}.git ({})'.format(proj, branch))
            return
        send('{}: Sorry, I didn\'t understand that.'.format(sender))

    bot.receive = handle_message

    bot.start()

if __name__ == '__main__':
    main()

