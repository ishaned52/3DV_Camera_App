from multiprocessing import Process
from time import sleep
import os
import cv2



class WorkerDifference(Process):

    def __init__(self, q):
        super().__init__()
        self.q = q
    

    def run(self):
        while True:
            print("run_diff")
            sleep(1)
            # if not self.q.empty():
            #     # diff = self.q.get()
            #     print("hhh")

            # else: 
            #     print("no values")