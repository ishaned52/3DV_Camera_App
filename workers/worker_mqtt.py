from cmath import e
import paho.mqtt.client as mqtt
import json
from multiprocessing import Process

from controls.settings import System

from controls.motor import MotorParameters

class WorkerMQTT(Process):
	def __init__(self, q):
		super().__init__()

		self.q = q
		self.sys = System()

		self.control_motor_left     = 0
		self.control_motor_right    = 0

		self.motors = MotorParameters()



		def on_connect(client, userdata, flags, rc):
			print("Connected with result code ", str(rc))
			# client.subscribe("$SYS/#")
			client.subscribe("3DV/#")
			# client.publish("online")
			     #   1) topic     2) message   
		
		
		def on_message(client, userdata, msg):

			m_decode= str(msg.payload.decode("utf-8","ignore"))

			print("Data received topic",str(msg.topic))
			print("Data received type",type(m_decode))
			print("Data received",m_decode)
			# print("Converting from Json to Object")
			try:
				control_message= json.loads(m_decode) #decode json data
				print("type _____:", type(control_message))
				# process command ----------------------------------------------
				

				object = int(control_message["lens_shift"]) 

				if object == 1 :		# Seperation
					self.control_motor_left =1
					self.control_motor_right=6
				if object == 2 :		# Tilt
					self.control_motor_left =2
					self.control_motor_right=5
				if object == 3 :		# Convergence
					self.control_motor_left =3
					self.control_motor_right=4


				
				direction_of_motor = int(control_message["direction"])
				nu_of_steps = int(control_message["steps"])
				
				move_action = bool(control_message["move"])


				# control_motor_left = control_message["m1"]
				# control_motor_right = control_message["m2"]
				control_side = str(control_message["control_side"])


# cmd = self.motors.move_steps(m1=self.control_motor_left, m2=self.control_motor_right, move=True, direction=direction_of_motor, steps=nu_of_steps)

				if control_side == 'L':
					cmd = self.motors.move_steps(m1=self.control_motor_left, move = move_action, direction=direction_of_motor, steps=nu_of_steps)

				if control_side == 'R':
					cmd = self.motors.move_steps(m1=self.control_motor_right, move = move_action, direction=direction_of_motor, steps=nu_of_steps)

				if control_side == 'LR':
					cmd = self.motors.move_steps(m1=self.control_motor_left, m2=self.control_motor_right, move = move_action, direction=direction_of_motor, steps=nu_of_steps)


				# --------------------------------------------------------------
				#self.q.put(json.dumps(m_decode)) 				# control_message["speed"]
				self.q.put(cmd) 
			except Exception:
				print("json parsing exception")
			
		print("mqtt initializing")
		self.client = mqtt.Client()
		self.client.on_connect = on_connect
		self.client.on_message = on_message
		self.client.username_pw_set(username= "kapraadmin", password= "kapraadmin")
		self.client.connect("139.162.50.185")

		self.client.publish("online", "Device online -intializing.............................", retain=True)  
	
		


	def run(self):
		self.client.loop_forever()


# 		(  "steps":100,   "direction":1 /0 , "move": START/STOP/HOME   , "controlSide": L,R ,LR , "lens_shift":1 /2 /3)



#				("steps":10 ,"direction":1 , "control_side":LR , "lens_shif":1, "move":True )


# chmod: cannot access '/dev/ttyUSB0': No such file or directory
# mqtt initializing
# Connected with result code  0
# Data received topic 3DV/
# Data received type <class 'str'>
# Data received {"power":215, "speed":255, "clockwise":0, "steps":100, "move":1}
# <class 'dict'>
# 66666666666666666666 : {'power': 215, 'speed': 255, 'clockwise': 0, 'steps': 100, 'move': 1}


# message ///////////>>> bytearray(b'\x01\x03\x00\x00\x00\x04\x02\x02\x00dh\x03\x04\x00\x00\x00dk\x04\x02\x00\x01\x07')