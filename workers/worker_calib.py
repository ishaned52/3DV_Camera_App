# import cv2

from multiprocessing import Process
from time import sleep
import cv2

class WorkerCalibrator(Process):
    def __init__(self, q1, q2):
        super().__init__()
        self.q1 = q1
        self.q2 = q2

    def run(self):
        while True:
            
            sleep(0.1)

            print("Running")

            if not self.q1.empty() and not self.q2.empty():
                frameL = self.q1.get()
                frameR = self.q2.get()

                abs_frame = cv2.absdiff(frameL, frameR)
                cv2.imshow('Absolute Difference', abs_frame)
            cv2.waitKey(1)
                