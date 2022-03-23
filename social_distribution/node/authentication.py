from operator import truediv
from author_manager.models import Author
from .models import Node
import base64


def basic_authentication(request):
    # local authentication
    local, remote = False, False
    try:
        # local authentication
        if not request.user.is_anonymous and Author.objects.filter(user=request.user).exists():
            local = True
            return local, remote
        else:
            auth_header = request.headers['Authorization']
            encoded_credentials = auth_header.split(' ')[-1]  # remove 'Basic'
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':')
            
            # if username == INCOMING_USERNAME and password == INCOMING_PASSWORD:
            #     remote = True
            #     return local, remote
            # else:
            #     return local, remote
            for node in Node.objects.all():
                if username == node.incoming_username and password == node.incoming_password:
                    remote = True
                    return local, remote
             
            return local, remote
            
    except Exception as e:
        return local, remote
    