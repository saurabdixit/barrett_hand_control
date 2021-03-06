#!/usr/bin/env python

import rospy
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import JointState
import numpy as np
from Tkinter import *

class combiner(object):
    def __init__(self):
        rospy.init_node('combiner',anonymous = True)
        self.vector = np.zeros([18])
        self.master = Tk()
        self.pub = rospy.Publisher('control_slider_values',Float32MultiArray,queue_size=1)
        self.sub_hand = rospy.Subscriber('/bhand/joint_states', JointState, self.subscribe_hand)
        self.sub_arm = rospy.Subscriber('/wam/joint_states', JointState, self.subscribe_wam)
        self.vector[17] = 0
        self.transform_hand()
        self.publishvalues()
    def subscribe_hand(self,joints_ang_hand):
        self.vector[9] = joints_ang_hand.position[3]
        self.vector[10] = joints_ang_hand.position[0]
        self.vector[11] = joints_ang_hand.position[4]
        self.vector[12] = joints_ang_hand.position[3]
        self.vector[13] = joints_ang_hand.position[1]
        self.vector[14] = joints_ang_hand.position[5]
        self.vector[15] = joints_ang_hand.position[2]
        self.vector[16] = joints_ang_hand.position[6]
    
    def subscribe_wam(self, joints_ang_wam):
        self.vector[0] = joints_ang_wam.position[0]
        self.vector[1] = joints_ang_wam.position[1]
        self.vector[2] = joints_ang_wam.position[2]
        self.vector[3] = joints_ang_wam.position[3]
        self.vector[4] = joints_ang_wam.position[4]
        self.vector[5] = joints_ang_wam.position[5]
        self.vector[6] = joints_ang_wam.position[6]

    def transform_hand(self):
        self.master.button = Button(self.master,text = "Double click to transform",height = 10, width=20,  command = self.toggle_17)
        self.master.button.pack()

    def toggle_17(self):
        if self.vector[17]==0:
            self.vector[17]=1
        else:
            self.vector[17]=0

    def publishvalues(self):
        while not rospy.is_shutdown():
            self.pub.publish(data = self.vector)
            self.master.update()

def main():
    output_generator = combiner()
if __name__=="__main__":
    main()
