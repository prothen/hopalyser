#!/usr/bin/env python3.8
"""

ZeroMQ custom message class serialisation and deserialisation using msgpack.

Author: Philipp Rothenhäusler, Stockholm 2020

"""

import time
import enum
import ctypes
import msgpack

class T:

    S2MS = 1.e3
    S2US = 1.e6
    S2NS = 1.e9

    MS2S = 1.e-3
    MS2US = 1.e3
    MS2NS = 1.e6

    US2S = 1.e-6
    US2MS = 1.e-3
    US2NS = 1.e3
    US2S = 1.e6

    NS2S = 1.e-9
    NS2MS = 1.e-6
    NS2US = 1.e-3

class HopATime:
    REL_EPOCH = time.time_ns()

    @staticmethod
    def time():
        return time.time_ns()

    def pretty(stamp):
        print(HopATime.REL_EPOCH)
        return "{0:2.3f}".format((stamp - HopATime.REL_EPOCH)*T.NS2S)

def ensure_list(input):
    return [input if isinstance(input, list) else [input]][0]

class MSG(object):
    """ Define the identifiers for message return types. """
    ERR = b"0"
    ACK = b"1"

class MSG_ID(object):
    """ Define the MSG_ID for different message types. """
    NONE = 0
    STATUS = 1
    CONNECTION_STATUS = 2
    PID = 3

class STATUS(object):
    """ Define the identifiers for available status requests. """
    # placeholder request
    NONE = 0
    # ping request determining latency
    PING = 1
    # trace request determining latency and hops
    TRACE = 2
    # bandwdith request determining the bandwidth
    BW = 4
    # determine remote target from pid (not yet implemented)
    HUNT = 8


class MetaMessage(object):
    """ Define ZeroMQ msgpack meta data with MSG_ID and timestamp """
    def __init__(self, ID):
        self._fields = ['_ID', '_stamp']
        self._ID = ID
        self._stamp = time.time_ns()

    def _init(self, *args, **kwargs):
        res_a = all([setattr(self, self._fields[i], value) for i, value in enumerate(args)])
        res_kw = all([setattr(self, key, value) for key, value in kwargs.items()])
        return res_a and res_kw

    def __str__(self):
        return self.__class__.__name__ + ":\n" + "".join(['{0} \t : \t{1}\n'.format(
            fi.ljust(20), getattr(self, fi)) for fi in (self._fields)])

    def _transport(self):
        """ Return elements to be encoded. """
        return [getattr(self, fi) for fi in self._fields]

    def encode(self):
        """ Return the bytestring for the class attributes using msgpack. """
        return msgpack.packb(self._transport())

    def fetch_decoded(self, decoded):
        """ Decode a byte string into the class attributes using msgpack. """
        [setattr(self, fi, vi) for fi, vi in zip(self._fields, decoded)]
        return self

    def decode(self, bin):
        """ Decode a byte string into the class attributes using msgpack. """
        return self.fetch_decoded(msgpack.unpackb(bin))

    def _add_field(self, name, initial_value):
        """ Define a new message field. """
        self._fields += [name]
        setattr(self, name, initial_value)

    def get_ID(self):
        return self._ID

    def get_time(self):
        return self._stamp


class StatusMsg(MetaMessage):
    """ Define a ZeroMQ compatible status message implementation.  """
    def __init__(self, status=STATUS.NONE):
        super().__init__(MSG_ID.STATUS)
        self._add_field('status', status)


class ConnectionStatusMsg(MetaMessage):
    """ Define a ZeroMQ compatible status message implementation.  """
    def __init__(self, latency_us=0, n_hops=0, latency_hops_us=0):
        super().__init__(MSG_ID.CONNECTION_STATUS)
        self._add_field('latency_us', latency_us)
        self._add_field('n_hops', n_hops)
        self._add_field('latency_hops_us', ensure_list(latency_us))

    def set_trace(self, latency_hops_us):
        """ Set received latency of hops of most recent TRACE. """
        self.latency_hops_us = ensure_list(latency_hops_us)
        self.n_hops = len(self.latency_hops_us)

    def set_bw(self, bw):
        """ Set most recent bandwidth statistics. """
        raise NotImplementedError


class PIDMsg(MetaMessage):
    """ Define a ZeroMQ compatible status message implementation.  """
    def __init__(self, pid=0):
        super().__init__(MSG_ID.PID)
        self._add_field('pid', pid)


class NotImplementedMsg:
    """Catches MSG_ID.NONE instantiation attempts."""
    def __init__(self):
        raise NotImplementedError


MSGS = {
    MSG_ID.NONE: NotImplementedMsg,
    MSG_ID.PID: PIDMsg,
    MSG_ID.STATUS: StatusMsg,
    MSG_ID.CONNECTION_STATUS: ConnectionStatusMsg,
}


def DECODE_HOPA_MSGS(bin):
    """ Return decoded message from binary stream.

        Note:
            This is a convenience function for low
            performance multi-purpose data channels.

            Clearly the detection and instantiation
            degrades the performance of the reception
            process. Knowing the datatype the class
            inherent method .decode(bin) is recommended.
    """
    res = msgpack.unpackb(bin)
    return HOPA_MSGS[res[0]]().fetch_decoded(res)


if __name__ ==  "__main__":
    print('Main: Start test.\n\n')
    print('Main: Message test.')
    msg_con = ConnectionStatusMsg(20, 2, [30, 252])
    print(msg_con)
    d = msg_con.encode()
    print('Encoded message:\n{}'.format(d))
    print(DECODE_HOPA_MSGS(d))
    msg_con_rec = ConnectionStatusMsg()
    print('Receiver placeholder message:\n {}'.format(msg_con_rec))
    msg_con_rec.decode(d)
    print('Decoded message into placeholder: \n{}'.format(msg_con_rec))
    print('Finished test of ConnectionStatusMsg\n\n')
    print('Main: Test ConnectionStatusMsg: \n{}'.format(ConnectionStatusMsg()))
    msg_rec = StatusMsg()
    print('The receiver message for the NONE status:\n{}'.format(msg_rec))
    msg = StatusMsg(STATUS.PING)
    print('The default message for the PING status:\n{}'.format(msg))
    msg_enc = msg.encode()
    print('The default message for the PING encoded:\n{}'.format(msg_enc))
    t0 = time.time()
    msg_rec.decode(msg_enc)
    tf = time.time() - t0
    print('Decoding time in ms: {0}'.format(tf*1.e3))
    print('The receiver message for the PING status:\n{}'.format(msg_rec))
    print('Main: Finished test.\n\n')

