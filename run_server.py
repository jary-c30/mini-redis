from gevent import monkey; monkey.patch_all()

from miniredis.server import Server

if __name__ == '__main__':
    server = Server()
    server.run()