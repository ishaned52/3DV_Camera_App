# import cv2

from multiprocessing import Process
from time import sleep
import cv2
import numpy as np
import time 

class WorkerVerticalDiff(Process):
    def __init__(self, q1, q2):
        super().__init__()
        self.q1 = q1
        self.q2 = q2

    def run(self):
        while True:
            time.sleep(1)
            self.captureFeatureMatch()

            # self.vertical_correction()

        pass
            
    def captureFeatureMatch(self):

                
        frameL = self.q1.get()
        frameR = self.q2.get()

        # frameL = cv2.cvtColor(frameL, cv2.COLOR_GRAY2RGB)
        # frameR = cv2.cvtColor(frameR, cv2.COLOR_GRAY2RGB)

        grayL = frameL
        grayR = frameR

        
        img_matches = self.vertical_correction(frameL, frameR, frameL, frameR)
        
        
        cv2.imshow('Feature Matching', img_matches)
            
        cv2.waitKey(1)

                
    def vertical_correction(self, frameL, frameR, grayL, grayR):
        orb = cv2.ORB_create()
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        
        kpL, desL = orb.detectAndCompute(grayL, None)
        kpR, desR = orb.detectAndCompute(grayR, None)


        
        # Match the descriptors between the frames
        matches = bf.match(desL, desR)
        matches = sorted(matches, key=lambda x: x.distance)
        
        if len(matches)>10:
            src_pts = np.float32([ kpL[m.queryIdx].pt for m in matches ]).reshape(-1,1,2)
            dst_pts = np.float32([ kpR[m.trainIdx].pt for m in matches ]).reshape(-1,1,2)

            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            matchesMask = mask.ravel().tolist()

            h,w = grayL.shape
            pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
            dst = cv2.perspectiveTransform(pts,M)

        else:
            print ("Not enough matches are found - %d/%d" % (len(matches), 10))
            matchesMask = None

        # Draw first 10 matches.
        img_matches = cv2.drawMatches(frameL, kpL, frameR, kpR, matches[:5], None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

        Tot_disparity = 0
        inlier = 1
        for s in range(0,10):
            if mask[s] == 1 :#the point at the index s is an inlier
                Tot_disparity += (src_pts[s,0,1] - dst_pts[s,0,1])
                inlier += 1
                
        difference = Tot_disparity // inlier
        print("Difference     ", difference)
        
        if difference < 0:
            cv2.arrowedLine(img_matches, (30, 410), (30, 460), (0, 255, 255), 9,  tipLength = 0.3)
            cv2.putText(img_matches, str(difference), (10, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        elif difference > 0:
            cv2.arrowedLine(img_matches, (1250, 10), (1250, 60), (0, 255, 255), 9,  tipLength = 0.3)
            cv2.putText(img_matches, str(difference), (1200, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        elif difference == 0:
            cv2.putText(img_matches, 'Vertically_Aligned', (0, 0), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            pass
            
        return img_matches