#!/usr/bin/env python
"""

Test of ZeroMQ TCP connection

Author: Philipp Rothenhäusler, Smart Mobility Lab KTH, Stockholm 2020

"""


import zmq
import time

HOST="192.168.1.91"

c = zmq.Context.instance()
s = c.socket(zmq.REP)
s.bind('tcp://{}:2000'.format(HOST))

if __name__ == "__main__":
    print('Start test')
    while True:
        print('Wait for request:')
        msg = s.recv()
        print('Received: {}'.format(msg))
        time.sleep(2)
        s.send(b"World")

