#!/usr/bin/env python

import random
import time

import rospy
from std_msgs.msg import Bool, Float32, Int32
from geometry_msgs.msg import Twist


LEFT = 0
CENTRE = 1
RIGHT = 2


class Controller:
    def __init__(self):
        rospy.init_node('controller')
        self.turn_vel = rospy.get_param('~turn_vel', 1)
        self.fwd_vel = rospy.get_param('~fwd_vel', 0.2)
        self.obstacle_range = rospy.get_param('~obstacle_range', 100)
        self.rate = rospy.Rate(rospy.get_param('~rate', 50))
        self.time_to_stop_turning = -1
        self.startup_time = time.time()
        self.startup_delay = rospy.get_param('~startup_delay', 2)
        self.started = False
        self.turn_twist = None
        self.last_ranges = {LEFT: None, CENTRE: None, RIGHT: None}
        rospy.Subscriber('ul_range', Float32, self.range_callback, callback_args=LEFT)
        rospy.Subscriber('uc_range', Float32, self.range_callback, callback_args=CENTRE)
        rospy.Subscriber('ur_range', Float32, self.range_callback, callback_args=RIGHT)
        self.twist_pub = rospy.Publisher('twist', Twist, queue_size=10)
        self.gled_pub = rospy.Publisher('green_led', Bool, queue_size=10)
        self.rled_pub = rospy.Publisher('red_led', Bool, queue_size=10)
        self.rled_flash_pub = rospy.Publisher('red_led_flash', Int32, queue_size=10)

    def spin(self):
        self.rled_flash_pub.publish(4)
        while not rospy.is_shutdown():
            self.publish_cmd()
            self.rate.sleep()

    def publish_cmd(self):
        if time.time() < self.startup_time + self.startup_delay:
            self.rled_flash_pub.publish(4)
            self.twist_pub.publish(Twist())
            return
        if any([r is None for r in self.last_ranges.values()]):
            # Still waiting for first reading from another sensor
            self.twist_pub.publish(Twist())
            return
        if not self.started:
            self.rled_flash_pub.publish(0)
            self.started = True
        if self.time_to_stop_turning > time.time():
            # Finish turning first
            self.twist_pub.publish(self.turn_twist)
            return
        else:
            if all([r > self.obstacle_range for r in self.last_ranges.values()]):
                # All clear, just go for it
                self.forward()
            else:
                self.turn_right()

    def forward(self):
        out = Twist()
        self.time_to_stop_turning = -1
        out.linear.x = self.fwd_vel
        self.gled_pub.publish(True)
        self.rled_pub.publish(False)
        self.twist_pub.publish(out)

    def turn_right(self):
        self.turn_twist = Twist()
        self.turn_twist.angular.z = -self.turn_vel
        self.time_to_stop_turning = time.time() + 1.6
        self.gled_pub.publish(False)
        self.rled_pub.publish(True)
        self.twist_pub.publish(self.turn_twist)

    def range_callback(self, msg, s):
        self.last_ranges[s] = msg.data


if __name__ == '__main__':
    try:
        controller = Controller()
        controller.spin()
    except rospy.ROSInterruptException:
        pass
