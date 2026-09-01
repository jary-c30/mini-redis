# mini-redis

A simplified Redis-like key-value server built from scratch using Python, implementing a custom binary wire protocol (based on Redis's RESP protocol) supporting integers, strings, arrays, and nested dictionaries. Built with [gevent](http://www.gevent.org/) for concurrent client handling.

This project is based on [this blog post by Charles Leifer](https://charlesleifer.com/blog/building-a-simple-redis-server-with-python/), extended and built independently as a learning project.

## Features
- Binary-safe wire protocol supporting binary data, integers, strings, arrays, and nested dictionaries
- Concurrent client handling using gevent
- Commands: `DELETE`, `GET`, `SET`, `FLUSH`, `MSET`, `MGET`
- Matching client library for interacting with the server

## Project file structure
```
miniredis/
├── exceptions.py    # custom exceptions
├── protocol.py      # wire protocol parsing and serialization
├── server.py        # server, connection handling, and command implementation
└── client.py        # client for connecting to and issuing commands
```

## Setup
If on Mac, you may need to type `python3` rather than `python`.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the server
Make sure you're in the `mini-redis` folder.

**Terminal 1:**
```bash
python3 run_server.py
```

## Using the client
Make sure you're in the `mini-redis` folder.

**Terminal 2** — open a Python interactive shell (`python3`), then:
```python
from miniredis.client import Client
client = Client()
client.set('key1', 'value1')
client.get('key1')                      # b'value1'
client.mset('k2', 'v2', 'k3', 'v3')
client.mget('k2', 'k3')                 # [b'v2', b'v3']
client.delete('key1')
client.flush()
```


## What I learned

Building this project has taught me how to work with raw TCP socket in python, along with designing and implementing a custom binary protocol from a specification, handle recursive parsing/serialization for nested data structures such as arrays/dictionaries, and finally building a functional client-server architecture from scratch.