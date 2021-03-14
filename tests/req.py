#!/usr/bin/env python
"""

Test of ZeroMQ TCP connection

Author: Philipp Rothenhäusler, Smart Mobility Lab KTH, Stockholm 2020

"""


import zmq
import time

HOST="192.168.1.91"

c = zmq.Context()
s = c.socket(zmq.REQ)
s.connect("tcp://{}:2000".format(HOST))

if __name__ == "__main__":
    print('Start test')
    while True:
        s.send(b"Hello ")
        print('sent request')
        msg = s.recv()
        print('Received ack:\n{}'.format(msg))
        time.sleep(2)

