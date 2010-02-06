import sys, getpass
from clients import SimpleSession, TeamRoom, MessageCenter,\
                    AuthenticationError


def header(text):
    print ''
    print '-' * len(text)
    print text
    print '-' * len(text)
    print ''

def raw_select(choices):
    choice = None
    numbers = ['0']
    print "Available options:\n"
    for n, item in enumerate(choices):
        print "[%d] %s" % (n+1, item)
        numbers.append(str(n+1))
    print "[0] [<< Back]\n"
    while choice not in numbers:
        choice = raw_input('Please select: ')
    return int(choice)-1


if __name__ == "__main__":
    from pprint import pprint

    while True:
        header('Please authenticate')
        username = raw_input('Username: ')
        password = getpass.getpass()
        session = SimpleSession(echo=False)
        try:
            session.login(username, password)
            break
        except AuthenticationError:
            print'\n> Wrong username or password. Please try again'

    print '\n> Logged in succesfully'
    while True:
        header('Main menu')
        choice = raw_select(['Message Center', 'Team Rooms'])
        if choice == 0:
            mc = MessageCenter(session)
            while True:
                header('Message Center')
                trays = mc.list()
                choices = ['[Compose Message]'] + ['%(type)s (%(unread)s)' % tray for tray in trays]
                choice = raw_select(choices)
                if choice == -1:
                    break
                elif choice == 0:
                    header('Composing message')
                    recipients = raw_input('Recipients (oDesk ids, comma-separated): ')
                    recipients = recipients.split(',')
                    subject =  raw_input('Subject: ')
                    body =  raw_input('Body: ')
                    mc.send(recipients, body, subject)
                    print "\n> Message was sent succesfully"
                else:
                    mc.select(trays[choice-1]['type'])
                    header('Message List')
                    for message in mc.messages():
                        print "%(subject)s" % message
                    print ''
                    choice = raw_select([])
        elif choice == 1:
            tr = TeamRoom(session)
            while True:
                header('Team Rooms')
                teams = tr.list()
                choice = raw_select(['%(name)s (%(id)s)' % team for team in teams])
                if choice == -1:
                    break
                tr.select(teams[choice]['id'])
                users = tr.users()
                header('User List')
                for user in users:
                    print "%(first_name)s %(last_name)s (%(uid)s) - %(role)s" % user
                print ''
                choice = raw_select([])
        else:
            break

