#!/usr/bin/env python

import random
import time

import rospy
from std_msgs.msg import Int32, Bool
from crues_actuators.msg import MotorControl

from crues import us
from crues.us import LEFT, CENTRE, RIGHT


mc_pub = rospy.Publisher('motor_control', MotorControl, queue_size=10)
gl_pub = rospy.Publisher('green_led', Bool, queue_size=10)
rl_pub = rospy.Publisher('red_led', Bool, queue_size=10)
time_to_stop_turning = -1
last_ranges = {LEFT: None, CENTRE: None, RIGHT: None}
turn_speed = 18
fwd_speed = 25
obstacle_range = 100


def _mc_msg(ls, rs):
    msg = MotorControl()
    msg.l_speed = ls
    msg.r_speed = rs
    msg.slp = False
    return msg


def handle_new_range(msg, s):
    r = msg.data
    global time_to_stop_turning
    last_ranges[s] = r
    #if any([r is None for r in last_ranges.values()]):
        # Still waiting for first reading from another sensor
    #    return
    if 0 < time_to_stop_turning < time.time():
        # Finish turning first
        return
    if all([r > obstacle_range for r in last_ranges.values()]):
        # All clear, just go for it
        mc_pub.publish(_mc_msg(fwd_speed, fwd_speed))
        gl_pub.publish(True)
        rl_pub.publish(False)
    elif last_ranges[LEFT] < last_ranges[RIGHT]:
        # Obstacle more on left, so turn right
        mc_pub.publish(_mc_msg(turn_speed, -turn_speed))
        time_to_stop_turning = time.time() + random.uniform(0.3, 0.6)
        gl_pub.publish(False)
        rl_pub.publish(True)
    else:
        # Obstacle more on right, so turn left
        mc_pub.publish(_mc_msg(-turn_speed, turn_speed))
        time_to_stop_turning = time.time() + random.uniform(0.3, 0.6)
        gl_pub.publish(False)
        rl_pub.publish(True)


def main():
    try:
        rospy.init_node('roomba')
        rospy.Subscriber('ul_range', Int32, handle_new_range, callback_args=LEFT)
        rospy.Subscriber('uc_range', Int32, handle_new_range, callback_args=CENTRE)
        rospy.Subscriber('ur_range', Int32, handle_new_range, callback_args=RIGHT)
        # spin() simply keeps python from exiting until this node is stopped
        rospy.spin()
    except rospy.ROSInterruptException as e:
        rospy.logerr("ROSInterruptException in node 'roomba'")
        rospy.logerr(e)


if __name__ == '__main__':
    main()