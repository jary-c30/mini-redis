from gevent import socket
from gevent.pool import Pool
from gevent.server import StreamServer

from miniredis.exceptions import CommandError, Disconnect
from miniredis.protocol import ProtocolHandler


#sets up the server with a pool to limit concurrent clients, along with the TCP server bound to host/port
class Server(object):
    def __init__(self, host='127.0.0.1', port=31337, max_client=64):
        self._pool = Pool(max_client)
        self._server = StreamServer((host, port), self.connection_handler, spawn=self._pool)
        self._protocol = ProtocolHandler()
        self._kv = {}
        self._commands = self.get_commands()

def connection_handler(self, conn, address):
    socket_file = conn.makefile('rwd')

    #an infinite loop
    while True:

        #if user disconnects from the server, program catches a break and stops proccessing
        try:
            data = self._protocol.handle_request(socket_file)
        except Disconnect:
            break

        #if use makes an error, it doesnt mean the user want to disconnect it just flags wrong command or other errors
        try:
            resp = self.get_response(data)
        except CommandError as exc:
            resp = Error(exc.args[0])

        #whatever resp ended being Error or successful it sends back to the user useing write_repsonse
        self._protocol.write_response(socket_file,resp)

#defining a dictionary of commands, building a lookup table
def get_commands(self):
    return {
        'GET': self.get,
        'SET': self.set,
        'DELETE': self.delete,
        'FLUSH': self.flush,
        'MGET': self.mget,
        'MSET': self.mset,
    }


def get_response(self, data):

    #if commands come as a plain string
    if not isinstance(data, list):
        data = data.split()

    #check if data is non-empty if not than riase command error with message
    if not isinstance(data, list) or not data:
        raise CommandError('Must be list or simple string')

    #first elemnt is always the command name, upper case it so get, Get, or GET are treated the same
    command = data[0].upper()

    #looking up the command name returns None if command is not recognized
    command_method = self._commands.get(command, None)

    if not command_method:
        raise CommandError('Unrecognized command: %s' % command)

    #call the command method unpacking the remaing elemts of data as single arguments
    #ex --> ['GET', 'key1'] is ['key1'] unpacked as command_method ('key1')
    return command_method(*data[1:])

def get(self, key):
    return self._kv.get(key)

def set(self, key, value):
    self._kv[key] = value
    return 1

def delete(self, key):
    if key in self._kv:
        del self._kv[key]
        return 1
    else:
        return 0