from gevent import socket

from miniredis.exceptions import CommandError
from miniredis.protocol import ProtocolHandler

class Client(object):
    def __init__(self, host='127.0.0.1', port=31337):
        self._protocol = ProtocolHandler()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))
        self._fh = self._socket.makefile('rwb')

    #args becomes ex. ('GET', 'key1')
    def execute(self, *args):

        #calls the serialization method since args is tuple it hits list/tuple branch or write
        self._protocol.write_response(self._fh, args)
        #reads bytes and pasres $ type
        resp = self._protocol.handle_request(self._fh)

        #check if resp is error 
        if isinstance(resp, Error):
            raise CommandError(resp.message)

        #returns the resp value
        return resp

    def get(self, key):
        return self.execute('GET', key)

    def set(self, key, value):
        return self.execute('SET', key, value)

    def delete(self, key):
        return self.execute('DELETE', key)

    def flush(self):
        return self.execute('FLUSH')

    def mget(self, *keys):
        return self.execute('MGET', *keys)

    def mset(self, *items):
        return self.execute('MSET', *items)





