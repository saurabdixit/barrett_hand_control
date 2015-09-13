#!/usr/bin/python

from openravepy import *
import rospy
import numpy as np
import csv
from stlwriter import *
import os
from stl import mesh

import rospkg

from shared_playback import *

stl_dest_dir = os.path.expanduser("~") + "/grasp_stls"
#grasp_data_directory = os.path.expanduser("~") + "/grasp_data"

class stl_generator():
    def __init__(self):
        self.env = Environment()
	#self.viewer = self.env.SetViewer('qtcoin')
	bhc_path = rospkg.RosPack().get_path('barrett_hand_control')
        robot_path = bhc_path + '/src/barrett_wam.dae'
	self.env.Load(robot_path)
        self.robot = self.env.GetRobots()[0]
	self.robot.SetTransform([[1,0,0,0],[0,1,0,0],[0,0,1,-1.16],[0,0,0,1]])
        self.vertices = np.array([])
        self.indices = np.array([])
        self.links = self.robot.GetLinks() 

    def set_joints(self, hand_joints, wam_joints):
	T_hand = np.array(hand_joints)
	T_wam = np.array(wam_joints)
	T_robot = T_wam[0:7]
	T_robot = np.append(T_robot,[0,0])
	T_robot = np.append(T_robot,[T_hand[3],T_hand[0],T_hand[4],T_hand[3],T_hand[1],T_hand[5],T_hand[2],T_hand[6]])
	self.robot.SetDOFValues(T_robot)

    def generate_stl(self, stl_out_path):
        if os.path.exists(stl_out_path):
		rospy.loginfo("STL already exists: " + stl_out_path)
		return
	all_vertices, all_faces = get_robot_points(self.robot)
	
	self.vertices = numpy.array(all_vertices)
	self.indices = numpy.array(all_faces)

	self.write_stl(stl_out_path)

	# Now try reading the same stl
	#robo_mesh = mesh.Mesh.from_file(stl_out_path)
	#print "Num stl vertices: ", len(robo_mesh.points)
	#print "Num vertices in trimesh: ", len(self.vertices)
	#print "first couple of trimesh points: ", self.vertices[0:6]
	#print "first couple of stl points: ", robo_mesh.points[0:6]
	#self.a = self.env.plot3(self.vertices[336576], 6)
	#self.b = self.env.plot3(self.vertices[403995], 6)
	#self.c = self.env.plot3(self.vertices[400798], 20)
	#raw_input("How do those numbers compare?")

    def write_stl(self, stl_out_path):
        faces_points = []
        for vec in self.indices:
            faces_points.append([self.vertices[vec[0]],self.vertices[vec[1]],self.vertices[vec[2]]])
        
        with open(stl_out_path,'wb') as fp:
            writer= Binary_STL_Writer(fp)
            writer.add_faces(faces_points)
            writer.close()

def get_robot_points(robot):
	links = robot.GetLinks()
	all_vertices = []
    	all_faces = []
    	ind = 0
	for link in links:
		vertices = link.GetCollisionData().vertices
		faces = link.GetCollisionData().indices
		if ind == 0:
		    faces = np.add(faces,ind)
		else:
		    faces = np.add(faces,ind+1)
		try:
		    ind = faces[-1][-1]
		except:
		    pass
		

		#print "link: ", link, "\nStarting index for this link: ", len(all_vertices)
		link_pose = poseFromMatrix(link.GetTransform())
		transform_vertices = poseTransformPoints(link_pose, vertices)
		all_vertices.extend(transform_vertices.tolist())
		all_faces.extend(faces.tolist())
	
	return all_vertices, all_faces


def write_stls(grasp_data_directory, stl_generator):
	global stl_dest_dir
	data_dirs = get_data_dirs(grasp_data_directory)
	for (data_dir_path, obj_num, sub_num) in data_dirs:
		# Open the snapshot bag
		snapshot_bag = None
		try:
			snapshot_bag = try_bag_open(data_dir_path + "/grasp_extreme_snapshots.bag")
		except IOError:
			rospy.logerr("Could not open snapshot bag for directory: " + data_dir_path)
			continue

		# Replay all messages
		for topic, msg, t in snapshot_bag.read_messages():
			if "good" in data_dir_path:
				stl_path = stl_dest_dir + "/" + "good"
			else:
				stl_path = stl_dest_dir + "/" + "bad"
				
			stl_path += "/" + "obj" + str(obj_num) + "_sub" + str(sub_num) + "_grasp" + str(msg.grasp_num)
			if msg.is_optimal:
				stl_path += "_optimal" + str(msg.optimal_num)
			else:
				stl_path += "_extreme" + str(msg.extreme_num)
			stl_path += "_robot.stl"
			
			rospy.loginfo("Saving stl " + stl_path)
			stl_generator.set_joints(msg.hand_joints.position, msg.wam_joints.position)
			stl_generator.generate_stl(stl_path)
		
		snapshot_bag.close()

if __name__=="__main__":
    rospy.init_node('stl_generator',anonymous=True)
    rospy.loginfo("Stl generator script online.")
    rospy.loginfo("Saving stls to " + stl_dest_dir + " and reading data from " + grasp_data_directory)
    
    generate_stl = stl_generator()
    
    if not os.path.exists(stl_dest_dir):
    	rospy.loginfo("Stl saving path does not exist, creating it.")
    	os.makedirs(stl_dest_dir + "/good")
    	os.makedirs(stl_dest_dir + "/bad")

    write_stls(grasp_data_directory, generate_stl)
    rospy.loginfo("STL conversions complete.")
