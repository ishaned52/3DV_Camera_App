import cv2
import numpy as np
from multiprocessing import Queue


class StereoCalibrator:
    def __init__(self, lq: Queue, rq: Queue) -> None:
        self.lq = lq
        self.rq = rq
        self.array_laplacianL = []
        self.array_laplacianR = []

    def capture_frames(self, process: int = 0):
        while True:
            if not self.lq.empty() and not self.rq.empty():
                frameL = self.lq.get()
                frameR = self.rq.get()

                grayL = cv2.cvtColor(frameL, cv2.COLOR_BGR2GRAY)
                grayR = cv2.cvtColor(frameR, cv2.COLOR_BGR2GRAY)

                if process == 0:
                    # do absolute difference
                    abs_frame = self.absolute_difference(grayL, grayR)
                    cv2.imshow("Absolute Difference", abs_frame)

                elif process == 1:
                    # do Blur Correction
                    frameL, self.array_laplacianL = self.blur_correction(frameL, grayL, self.array_laplacianL)
                    frameR, self.array_laplacianR = self.blur_correction(frameR, grayR, self.array_laplacianR)
                    cv2.imshow("Blur Frame Left ", frameL)
                    cv2.imshow("Blur Frame Right ", frameR)

                elif process == 2:
                    # do Vertical Correction
                    img_matches = self.vertical_correction(frameL, frameR, grayL, grayR)
                    cv2.imshow("Feature Matching", img_matches)

                else:
                    pass

            cv2.waitKey(1)

    def vertical_correction(self, frame_l, frame_r, gray_l, gray_r):
        orb = cv2.ORB_create()
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

        kp_l, des_l = orb.detectAndCompute(gray_l, None)
        kp_r, des_r = orb.detectAndCompute(gray_r, None)

        # Match the descriptors between the frames
        matches = bf.match(des_l, des_r)
        matches = sorted(matches, key=lambda x: x.distance)

        if len(matches) > 10:
            src_pts = np.float32([kp_l[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp_r[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

            # Remove cross points
            threshold = 10  # Adjust threshold value as needed
            src_pts_filtered = []
            dst_pts_filtered = []
            for i in range(len(matches)):
                if abs(src_pts[i, 0, 0] - dst_pts[i, 0, 0]) > threshold:
                    src_pts_filtered.append(src_pts[i])
                    dst_pts_filtered.append(dst_pts[i])
            src_pts_filtered = np.array(src_pts_filtered)
            dst_pts_filtered = np.array(dst_pts_filtered)

            M, mask = cv2.findHomography(src_pts_filtered, dst_pts_filtered, cv2.RANSAC, 5.0)


        else:
            print("Not enough matches are found - %d/%d" % (len(matches), 10))

        # Draw first 10 matches.
        img_matches = cv2.drawMatches( frame_l, kp_l, frame_r, kp_r, matches[:15], None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,)

        total_disparity = 0
        inliers = 0
        for s in range(min(10, len(mask))):
            if mask[s] == 1:  # the point at index s is an inlier
                total_disparity += src_pts_filtered[s, 0, 1] - dst_pts_filtered[s, 0, 1]
                inliers += 1

        if inliers > 0:
            difference = total_disparity // inliers
            print("Difference:", difference)

            if difference < 0:
                cv2.arrowedLine(img_matches, (30, 410), (30, 460), (0, 255, 255), 9, tipLength=0.3)
                cv2.putText(img_matches, str(difference), (10, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2,)
            elif difference > 0:
                cv2.arrowedLine(img_matches, (1250, 10), (1250, 60), (0, 255, 255), 9, tipLength=0.3)
                cv2.putText(img_matches, str(difference), (1200, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2,)
            else:
                cv2.putText(img_matches, "Vertically_Aligned", (0, 0), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,)
        else:
            cv2.putText(img_matches, "No inliers found", (0, 0), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2,)

        return img_matches

    def horizontal_correction(self):
        pass

    def blur_correction(
        self, frame, gray, array_laplacian, blur_max: int = 55, blur_min: int = 25
    ):
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        array_laplacian.append(np.var(laplacian))

        if len(array_laplacian) >= 5:
            avg_laplacian = sum(array_laplacian) / len(array_laplacian)
            print("avg_laplacian", avg_laplacian)
            del array_laplacian

            if avg_laplacian > blur_max:  # over sharp
                cv2.putText(
                    frame,
                    "Over Sharp",
                    (150, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 0),
                    2,
                )
                cv2.circle(frame, (100, 100), 25, (0, 0, 0), -1)
            elif avg_laplacian < blur_min:  # blur
                cv2.putText(
                    frame,
                    "Blur",
                    (150, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )
                cv2.circle(frame, (100, 100), 25, (0, 0, 255), -1)
            else:
                cv2.putText(
                    frame,
                    "OKAY",
                    (150, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )
                cv2.circle(frame, (100, 100), 25, (0, 255, 0), -1)

        try:
            return (frame, array_laplacian)

        except:
            return (frame, [])

    def absolute_difference(self, grayL, grayR):
        diff = cv2.absdiff(grayL, grayR)

        return diff
