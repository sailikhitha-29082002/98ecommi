from itsdangerous import URLSafeTimedSerializer
from key import salt
def encode(data):
    serializer=URLSafeTimedSerializer('likhitha')
    return serializer.dumps(data,salt=salt)  #dumps : Tokenize/Encrypts the data
def decode(data):
    serializer=URLSafeTimedSerializer('likhitha')
    return serializer.loads(data,salt=salt)
