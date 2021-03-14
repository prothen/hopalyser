"""

ROS interface for network analyzer utilities in compact event loop with intra process interface
using ZeroMQ.


Author: Philipp Rothenhäusler, Stockholm 2020

"""
import sys
import attr
import rospy
import signal
import typing


from hopalyser import core

from hopalyser_msgs.msg import Status
from hopalyser_msgs.msg import ConnectionStatus

@attr.s
class ROSInterface(object):
    """ ROS1 middleware wrapper for ZeroMQ based NetworkAnalyzer.  """
    _debug_is_enabled = attr.ib(default=False, type=bool)

    def __attrs_post_init__(self):
        rospy.init_node("hopalyser")
        # Fetch update frequency of current status request
        frequency = rospy.get_param("~analyze/frequency", 1)
        # Fetch desired target from rosparam
        target = rospy.get_param("~analyze/target", "1.1.1.1")

        # Fetch activation on pid
        wait_for_pid  = rospy.get_param(
                "~analyze/wait_for_pid", False)
        wait_for_meta_topic  = rospy.get_param(
                "~analyze/wait_for_meta_topic", False)
        meta_topic = rospy.get_param(
                "~analyze/meta_topic", "~failed_to_fetch_meta_topic")

        print('Executing analyzer node with:')
        print('Target:              \t{}'.format(target))
        print('Frequency:           \t{}'.format(frequency))
        print('Wait for pid:        \t{}'.format(wait_for_pid))
        print('Wait for meta topic: \t{}'.format(wait_for_meta_topic))
        print('-> meta_topic:       \t{}'.format(meta_topic))

        target = [target if not wait_for_meta_topic else
                  self._wait_for_meta_topic(meta_topic)][0]

        # Initialise ZeroMQ based analyzer
        self._analyzer = core.NetworkAnalyzer(target=target,
                                              wait_for_pid=wait_for_pid)
        self._analyzer.dispatch()
        self._deadline_next_request = rospy.Time.now()
        self._loop = rospy.Rate(frequency)
        self._status = Status()
        self._connection_status = ConnectionStatus()
        rospy.Subscriber("~request", Status, self._cb_request)
        self._pub_connection_status = rospy.Publisher("~connection_status", ConnectionStatus, queue_size=5)
        signal.signal(signal.SIGINT, self._farewell)
        signal.signal(signal.SIGTERM, self._farewell)

    @staticmethod
    def _wait_for_meta_topic(wait_topic):
        """ Wait for reception of topic on meta_topic. """
        target = None
        def cb(msg):
            nonlocal target
            print('Received target from meta_topic')
            target = msg.peerStats.IP
            print(target)
        loop = rospy.Rate(0.5)
        wait_sub = rospy.Subscriber(wait_topic, RTCStats, cb)
        while target is None:
            print('Target in loop: {}'.format(target))
            loop.sleep()
        wait_sub.unregister()

        return target

    def _set_next_request_deadline(self):
        """ Schedule the next update request to the analyzer event loop. """
        self._deadline_next_request = rospy.Time.now() + self._loop.sleep_dur

    @staticmethod
    def _farewell(sig, frame):
        print('Encounter SIGINT or SIGTERM. Closing now. ')
        sys.exit(1)

    def _cb_request(self, request):
        """ Parse ROS message into ZMQ interface compatible status type. """
        if self._debug_is_enabled:
            print('Received request: {0}'.format(request))
        self._status = request.status
        if self._status & Status.NONE:
            pass
        if self._status & Status.PING:
            self._analyzer.request(Status.PING)
        if self._status & Status.TRACE:
            self._analyzer.request(Status.TRACE)
        if self._status & Status.BW:
            print('Warning: Not implemented')
        self._set_next_request_deadline()

    def _automated_request(self):
        """ Request update if frequency is nonzero. """
        if self._deadline_next_request < rospy.Time.now():
            self._analyzer.request(Status.PING)
            self._analyzer.request(Status.TRACE)
            self._set_next_request_deadline()

    def _publish_connection_status(self):
        """ Publish most recent received status. """
        self._pub_connection_status.publish(self._connection_status)

    def _update_status(self):
        """ Send status update request via ZMQ interface. """
        cs_mq = self._analyzer.get_connection_status()
        self._connection_status.stamp = rospy.Time.now()
        self._connection_status.latency_us = int(cs_mq.latency_us)
        self._connection_status.n_hops = int(cs_mq.n_hops)
        self._connection_status.latency_hops_us = [int(ei) for ei in cs_mq.latency_hops_us]

    def run(self):
        """ Run the main ROS middleware loop. """

        while not rospy.is_shutdown():
            self._automated_request()
            self._update_status()
            self._publish_connection_status()
            self._loop.sleep()


if __name__  == "__main__":
    # Test ZeroMQ class
    t = NetworkAnalyzer(target="localhost")
    t.dispatch()
    print('success')

    # Library testbed
    test = ROSInterface()
    test.run()
