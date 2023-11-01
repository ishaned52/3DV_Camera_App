import serial
import subprocess

from multiprocessing import Process
from time import sleep

from controls.settings import System

class WorkerSerial():
	def __init__(self, q):
		super().__init__()
		
		self.q = q
		self.sys = System()
		
		subprocess.call(["echo {0} | sudo -S chmod o+rw {1}".format(self.sys.password, self.sys.PORT)], shell=True)
		sleep(0.1)
		subprocess.call(["stty {0} -F {1}".format(self.sys.BAUD_RATE, self.sys.PORT)], shell=True)
		sleep(0.1)
		#subprocess.call(["echo {1} | sudo -S chown {0} {2}".format(self.sys.username, self.sys.password, self.sys.PORT)], shell=True)
		
		self.run()
	def run(self):
		
		while True:
			print("iiiiiiiiiiiiii")
			sleep(0.1)
			if not self.q.empty():
				
				cmd = self.q.get()
				print("send >>> ", ''.join('{:02x}'.format(x) for x in cmd))
				with serial.Serial(self.sys.PORT, self.sys.BAUD_RATE, timeout=2) as ser:
					ser.write(cmd)
				print(cmd)
