import urllib, urllib2
import hashlib
from pprint import pprint
try:
    import json
except ImportError:
    import simplejson as json


def signed_urlencode(secret,query):
    """
    Converts a mapping object to signed url query

    >>> signed_urlencode('some$ecret', {})
    'api_sig=5da1f8922171fbeffff953b773bcdc7f'
    >>> signed_urlencode('some$ecret', {'spam':42,'foo':'bar'})
    'api_sig=11b1fc2e6555297bdc144aed0a5e641c&foo=bar&spam=42'
    """
    message = secret
    for key in sorted(query.keys()):
        message += str(key) + str(query[key])
    query['api_sig'] = hashlib.md5(message).hexdigest()
    return urllib.urlencode(query)


class AuthenticationError(Exception):
    pass

class NotAuthenticatedError(Exception):
    pass

class AccessForbiddenError(Exception):
    pass

class Session(object):

    version = 1
    base_url = 'https://www.odesk.com/api/'

    def __init__(self, public_key, secret_key):
        self.public_key = public_key
        self.secret_key = secret_key
        self.session_id = None

    def get_frobs(self, format='json'):
        url = self.base_url+'keys/frobs.'+format
        params = {'api_key': self.public_key}
        return urllib.urlopen(url+'?'+signed_urlencode(self.secret_key,params))

class SimpleSession(object):

    version = 1
    base_url = 'https://www.odesk.com/api/'

    def __init__(self, echo=False):
        self.session_id = None
        self.echo = echo

    def request(self, api_name, action, query=None, post_data=None):
        url = self.base_url + '%s/v%s/%s.json' % (api_name, self.version, 
                                                  action)
        if query is None:
            query = {}
        if self.session_id:
            query['session_id'] = self.session_id
        else:
            if action != 'login':
                raise NotAuthenticatedError("You should authenticate first")
        if query:
            url += '?'+urllib.urlencode(query)
        if self.echo:
            print url
        if post_data:
            post_data = urllib.urlencode(post_data)
        try:
            response = urllib2.urlopen(url, post_data)
        except urllib2.HTTPError, e:
            if e.code == 401:
                if self.session_id:
                    raise NotAllowedError('Access forbidden')
                else:
                    raise AuthenticationError('Wrong username or password')
            raise e
        try:
            result = json.loads(response.read())
        except Exception, e:
            raise e #FIXME
        if self.echo:
            pprint(result)
        return result

    def login(self, username, password):
        self.username = username
        data = {'username': username, 'password': password}
        result = self.request('auth','login', post_data=data)
        self.session_id = result['session']['session_id']


class BaseClient(object):
    
    def __init__(self, session):
        self.session = session

    def request(self, action, query=None, post_data=None):
        return self.session.request(self.api_name, action, query, post_data)



class TeamRoom(BaseClient):

    api_name = 'team'

    def __init__(self, *args, **kwargs):
        super(TeamRoom, self).__init__(*args, **kwargs)
        self.team_id = None

    def list(self):
        action = 'teamrooms'
        return self.request(action)['teamrooms']['teamroom']

    def list_ids(self):
        return [team['id'] for team in self.list()]

    def select(self, team_id):
        self.team_id = team_id

    def snapshots(self, online='now'):
        action = 'teamrooms/' + self.team_id
        return self.request(action, query={'online':online})

    def users(self):
        result = self.snapshots(online='all')
        lst = []
        snapshots = result['teamroom']['snapshot']
        if isinstance(snapshots, list):
            for snapshot in snapshots:
                item = snapshot['user'].copy()
                item['role'] = snapshot['role']
                lst.append(item)
        else:
            item = snapshots['user'].copy()
            item['role'] = snapshots['role']
            lst.append(item)
        return lst

class MessageCenter(BaseClient):

    api_name = 'mc'

    def __init__(self, *args, **kwargs):
        super(MessageCenter, self).__init__(*args, **kwargs)
        self.tray_type = None

    def list(self):
        action = 'trays'
        return self.request(action)['trays']

    def select(self, tray_type):
        self.tray_type = tray_type

    def messages(self):
        action = 'trays/%s/%s' % (self.session.username, self.tray_type)
        return self.request(action)['current_tray']['threads']

    def send(self, recipients, body, subject='', thread_id=None):
        action = 'threads/' + self.session.username
        # FIXME: It's unclear how to encode arrays for oDesk to accept, 
        # so using only first recipient for now
        post_data = { 'recipients': recipients[0], 'body': body, 
                      'subject': subject } 
        if thread_id:
            action += '/%s' % thread_id
            post_data['thread_id'] = thread_id
        return self.request(action, post_data = post_data)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
