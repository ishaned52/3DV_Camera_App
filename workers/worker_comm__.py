import serial
import subprocess

from multiprocessing import Process
from time import sleep
from controls.settings import System

class WorkerComm(Process):
	def __init__(self, q):
		super().__init__()

		self.q = q
		self.sys = System()
		# self.serialString = None
		
		subprocess.call(["echo {0} | sudo -S chmod o+rw {1}".format(self.sys.password, self.sys.PORT)], shell=True)
		#subprocess.call(["echo {1} | sudo -S chown {0} {2}".format(self.sys.username, self.sys.password, self.sys.PORT)], shell=True)
		
		sleep(.5)
		self.serialPort = serial.Serial(port=str(self.sys.PORT), baudrate=int(self.sys.BAUD_RATE), bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
		
	def run(self):
		while True:
			if not self.q.empty():
				cmd = self.q.get()
				print("send >>>", ''.join('{:02x}'.format(x) for x in cmd))
				self.serialPort.write(cmd)

			if(self.serialPort.in_waiting > 0):
				# out = self.serialPort.read_all() #reads whatever available
				# out = self.serialPort.readall() #reads all once received
				out = self.serialPort.readline() #reads a line ended with new line character
				print("rcve <<<", ''.join('{:02x}'.format(x) for x in out))
				
				
