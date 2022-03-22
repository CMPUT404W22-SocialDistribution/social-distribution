from operator import truediv
from author_manager.models import Author
from .models import Node
import base64

INCOMING_USERNAME = 'cmput404'
INCOMING_PASSWORD = 'cmput404'

def basic_authentication(request):
    # local authentication
    local, remote = False, False
    try:
        # local authentication
        if Author.objects.filter(user=request.user).exists():
            local = True
            return local, remote
        else:
            auth_header = request.META['HTTP_AUTHORIZATION']

            encoded_credentials = auth_header.split(' ')[-1]  # remove 'Basic'
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':')

            if username == INCOMING_USERNAME and password == INCOMING_PASSWORD:
                remote = True
                return local, remote
            else:
                return local, remote
    except:
        return local, remote
    