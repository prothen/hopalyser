#!/usr/bin/env python3.8
"""

Network analyzer utilities in compact event loop with intra process interface
using ZeroMQ.

Todo:
    - Add synchronise method (receive timestamp and compare with own timestamp)


Author: Philipp Rothenhäusler, Stockholm 2020

"""

import os

import zmq
import attr
import typing
import asyncio
import mtrpacket

from concurrent.futures import ProcessPoolExecutor


from hopalyser.msgs import HopATime
from hopalyser.msgs import T
from hopalyser.msgs import MSG
from hopalyser.msgs import MSG_ID
from hopalyser.msgs import STATUS
from hopalyser.msgs import StatusMsg
from hopalyser.msgs import ConnectionStatusMsg


@attr.s
class NetworkAnalyzer(object):
    """ Provide essential network analysis tools for ping and trace.
        Note:
            Middleware deployment agnostic base class using ZeroMQ.
            zmq.NOBLOCK as recv flag
        Todo:
            Add bw tracking requests based on PID
            Add time synchronisation
    """
    frequency = attr.ib(default=20, type=float)

    _pid = attr.ib(default=None, type=typing.Optional[int])
    _target = attr.ib(default=None, type=typing.Optional[str])
    _device_name = attr.ib(default="default", type=typing.Optional[str])
    _debug_is_enabled = attr.ib(default=False, type=typing.Optional[bool])

    ## Wait for process id to facilitate intra process instantiation and
    ## tracking of process specific bandwidth consumpction (Unsupported atm)
    _wait_for_pid = attr.ib(default=False, type=typing.Optional[bool])

    def __attrs_post_init__(self):
        # if wait for pid is true but pid supplied get target from pid
        ## Template for OS PID initiated tracking
        # self._pid = [os.getpid() if not wait_for_pid and pid is None
        #              else self._pid][0]
        # self._PID_AVAILABLE = [self._pid is not None][0]
        # Define the amount of extra hops that we send ICMP msgs to
        self._explore_hops = 10
        self._loop_dt = self.frequency**(-1)
        self._deadline_next_loop = self.time() + self._loop_dt*T.S2NS

        self._status = StatusMsg(STATUS.NONE)
        self._request_status = StatusMsg(STATUS.NONE)
        self._connection_status = ConnectionStatusMsg()
        # Define active request lookup
        self._request_active = {
            STATUS.NONE: False,
            STATUS.PING: False,
            STATUS.TRACE: False,
            STATUS.BW: False,
        }
        # Define available status commands
        self._request = {
            STATUS.NONE: self._handle_none,
            STATUS.PING: self._handle_ping,
            STATUS.TRACE: self._handle_trace,
            STATUS.BW: self._handle_bw
        }
        self._if_pid = None
        self._if_request = None
        self._if_request_status = None
        self._if_connection_status = None
        self._initialise_if_request_status()
        self._STATUS_OK = False

    @staticmethod
    def time():
        """ Return time with convenience timer wrapper.
            Note:
                Define all implementations based on this timer module.
                -> See PEP564: on Linux 84ns precision Python (>=3.7)
        """
        return HopATime.time()

    def get_device_name(self):
        """ Return the device name for the ZeroMQ asyncio interface. """
        return self._device_name

    def get_connection_status(self):
        """ Return locally the most recent ConnectionStatusMsg. """
        return self._connection_status

    def request(self, status_request, noblock=False):
        """ Request a new service routine from the event loop.
            Note:
                This method provides local interaction with the multi
                -processed event loop.
                This allows asynchronous interaction with event based
                triggers from the asyncio loop
            Todo:
                Add non-blocking optionn
        """
        if self._debug_is_enabled:
            print('ZMQ received the request: {0}'.format(status_request))
        self._request_status.status = status_request
        self._if_request_status.send(self._request_status.encode())
        if self._debug_is_enabled:
            print('Main thread: Send to asyncio loop:\n{}'.format(self._request_status))
        return self._if_request_status.recv() == MSG.ACK

    def _initialise_if_request_status(self):
        """ Initialise the request interface. """
        s = zmq.Context().socket(zmq.REQ)
        s.connect("ipc://{}".format(self._device_name))
        self._if_request_status =  s

    def _pid_listener(self):
        """ Wait for ZeroMQ request to update PID from external location.
            Todo:
                Define PID message
        """
        # Todo: Unsupported at the moment
        if self._pid is None:
            pid_addr = self._device_name + '_pid'
            print("Waiting for ZeroMQ PID activation "
                "on device address:\n{0}".format(pid_addr))
            self._if_pid = zmq.Context().socket(zmq.REP)
            self._if_pid.bind("ipc://{}".format(pid_addr))
            print('MP: wait for ZMQ service call')
            msg = DECODE_HOPA_MSGS(self._if_pid.recv())
            print('MP: Received: \n{0}'.format(msg))
            socket.send(MSG.ACK)
            # todo: fetch target and start bw tracking using nethogs
        return self._pid_target()

    def _pid_target(pid):
        """ Fetch remote target for supplied pid.  """
        raise NotImplementedError

    def dispatch(self):
        """ Dispatch the analyser node into its asynchronous event loop.
            Note:
                The event loop is launched in another process.
        """
        ex = ProcessPoolExecutor(max_workers=1)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._jumpad(ex))
        return self

    @staticmethod
    def _mp(_corout, *args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.ensure_future(_corout(*args))
        loop.run_forever()

    async def _jumpad(self, ex):
        asyncio.get_event_loop().run_in_executor(None, self._mp, self._run)
        await asyncio.sleep(1)

    async def _on_exit(self):
        """ Trigger the termination of the event loop. """
        print('Termination triggered.')
        asyncio.get_event_loop().stop()

    async def _handle_none(self, fut):
        """ Callback for NONE type request.  """
        fut.set_result(STATUS.NONE)
        return fut

    async def _handle_ping(self, fut):
        """ Callback for PING type request. """
        if self._request_active[STATUS.PING]:
            if self._debug_is_enabled:
                print('PING request in process. SKIPPING')
            return fut
        # self._request_active[STATUS.PING] = True
        ret = await self._ping(fut)
        #self._request_active[STATUS.PING] = False
        fut.set_result(ret)
        return fut

    async def _handle_trace(self, fut):
        """ Callback for TRACE type request.  """
        if self._request_active[STATUS.TRACE]:
            if self._debug_is_enabled:
                print('TRACE request in process. SKIPPING')
            return fut
        # self._request_active[STATUS.TRACE] = True
        ret = await self._trace(fut)
        # self._request_active[STATUS.TRACE] = False
        fut.set_result(ret)
        return fut

    async def _handle_bw(self, fut):
        """ Callback for BW type request.  """
        if not self._PID_AVAILABLE:
            print('Missing process ID to track bandwidth.')
            return
        raise NotImplementedError

    async def _ping(self, fut):
        """ Return latency to target in ms. """
        try:
            loop = asyncio.get_event_loop()
            asyncio.get_child_watcher().attach_loop(loop)
            async with mtrpacket.MtrPacket() as mtr:
                res = await mtr.probe(self._target, timeout=1)
            if res.success:
                self._connection_status.latency_us =res.time_ms*T.MS2US
        except Exception as e:
            self._STATUS_OK = False
            print('Encountered exception:\n{}'.format(e))
            self._request_active[STATUS.PING] = False

    async def _trace(self, fut):
        """ Return the amount of hops until target is reached. """
        try:
            n_hopsplore = self._connection_status.n_hops +  self._explore_hops
            async with mtrpacket.MtrPacket() as mtr:
                async def probe_me(ttl):
                    probe = await mtr.probe(self._target, protocol='udp',port=2000, ttl=ttl, timeout=1)
                    return (ttl, probe)
                tasks = [probe_me(i) for i in range(2, n_hopsplore)]
                res = await asyncio.gather(*tasks)
                lats = []
                for i in range(n_hopsplore-2):
                    if self._debug_is_enabled:
                        print('it: {0} with result: {1}'.format(i, res[i][1].result))
                        print('lats: {0}'.format(lats))
                    r = res[i][1]
                    if r.result == 'no-reply' or r.success or i == n_hopsplore -3:
                        lats = [[r.time_ms * T.MS2US] if not len(lats) else lats][0]
                        self._connection_status.set_trace(lats)
                        if self._debug_is_enabled:
                            print('Trace result:\n{}'.format(self._connection_status))
                        return True
                    else:
                        lats += [res[i][1].time_ms * T.MS2US]
        except Exception as e:
            print('Error message: {0}'.format(e))
            self._request_active[STATUS.TRACE] = False

    async def _next_loop(self):
        await asyncio.sleep(max(0, (self._deadline_next_loop - self.time())*T.NS2S))
        self._deadline_next_loop = self.time() + self._loop_dt

    async def _callback_interface(self):
        """ Wait for ZeroMQ service and return result. """
        if_req = self._if_request
        if self._debug_is_enabled:
            print('ZeroMQ wait for new request.')
        self._status.decode(if_req.recv())
        if_req.send(MSG.ACK)
        return self._status.status

    async def _run(self):
        """ Run the main asynchronous event loop with ZeroMQ service. """
        try:
            if_request = zmq.Context().socket(zmq.REP)
            if_request.bind("ipc://{}".format(self._device_name))
            self._if_request = if_request
            loop = asyncio.get_event_loop()
            self._STATUS_OK = True
            while self._STATUS_OK:
                fut = loop.create_future()
                req = self._request[(await self._callback_interface())](fut)
                await req
                #asyncio.create_task(req)
                #await self._next_loop()
        except Exception as e:
            print('AS: Encountered exception:\n{}'.format(e))
            await self._on_exit()


if __name__  == "__main__":
    # Test ZeroMQ class
    HOST = "34.199.231.194" # Heroku server (USA) - drops PING requests

    HOST = "1.1.1.1" # DNS server
    #HOST = "localhost"
    t = NetworkAnalyzer(target=HOST).dispatch()
    request = STATUS.PING
    import time
    while True:
        if t.request(STATUS.PING):
            print('Successful request.')
            print(t.get_connection_status())
        if t.request(STATUS.TRACE):
            print('Successful request.')
            print(t.get_connection_status())
        time.sleep(0.1)
