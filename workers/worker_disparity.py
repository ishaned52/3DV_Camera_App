import cv2
import numpy as np


class verDisparity():
    def __init__(self) -> None:
        self.capL=None
        self.capR=None

    def start(self):

        self.capL = cv2.VideoCapture()
        self.capR = cv2.VideoCapture()

        self.capL.open(0, cv2.CAP_V4L2)
        self.capR.open(1, cv2.CAP_V4L2)

        # self.capL.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        # self.capL.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        # self.capR.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        # self.capR.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not self.capL.isOpened():
            self.stop()
        if not self.capR.isOpened():
            self.stop()


        while (True):
            retL, frame1 = self.capL.read()
            retR, frame2 = self.capR.read()
            # ret1, frame1 = cap1.read()
            # ret2, frame2 = cap2.read()

            # if capL == False and self.capR == False :
            #     break

            # crop_image1 = frame1[140:340, 220:420]
            # crop_image2 = frame2[140:340, 220:420]

            gray_img1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray_img2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

            # Initiate ORB detector
            orb = cv2.ORB_create()

            # find the keypoints and descriptors with ORB
            kp1, des1 = orb.detectAndCompute(gray_img1, None)
            kp2, des2 = orb.detectAndCompute(gray_img2, None)

            # create BFMatcher object
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

            # Match descriptors.
            matches = bf.match(des1, des2)
            matches = sorted(matches, key=lambda x: x.distance)

            if len(matches)>10:
                src_pts = np.float32([ kp1[m.queryIdx].pt for m in matches ]).reshape(-1,1,2)
                dst_pts = np.float32([ kp2[m.trainIdx].pt for m in matches ]).reshape(-1,1,2)

                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
                matchesMask = mask.ravel().tolist()

                h,w = gray_img1.shape
                pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
                dst = cv2.perspectiveTransform(pts,M)

            else:
                print ("Not enough matches are found - %d/%d" % (len(matches),10))
                matchesMask = None

            # Draw first 10 matches.
            matching_result = cv2.drawMatches(gray_img1, kp1, gray_img2, kp2, matches[:10], None)

            Tot_disparity = 0
            inlier = 1
            for s in range(0,10):
                if mask[s] == 1 :#the point at the index s is an inlier
                    Tot_disparity += (src_pts[s,0,1]- dst_pts[s,0,1])
                    inlier += 1
            disparity = Tot_disparity/inlier
            print("ONE FRAME disparity     ", disparity)

            cv2.imshow("matching_result", matching_result)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.capL.release()
                self.capR.release()
                break

        self.stop()

    def stop(self):
        cv2.destroyAllWindows()
        
        if self.capL is not None:
            self.capL.release()
        if self.capR is not None:
            self.capR.release()

        self.capL=None
        self.capR=None 
