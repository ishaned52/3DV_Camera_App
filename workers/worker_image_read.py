from multiprocessing import Process
from time import sleep
import os
import cv2



class WorkerImageReader(Process):

    def __init__(self, q):
        super().__init__()
        self.q = q
    

    def run(self):
        while True:
            print("run")
            sleep(2)