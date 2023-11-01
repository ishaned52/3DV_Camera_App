import cv2
from controls.settings import AISettings, Camera, Motor
from controls.motor import MotorParameters
import numpy as np
import pandas as pd
from Main_Pipeline import CameraStreamer
import time

model = "new"


configPath = 'config/ai/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'
weightsPath = 'config/ai/frozen_inference_graph.pb'

classNames = []
classFile = 'config/ai/coco.names'


with open(classFile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)


class TimerCallbacks:

    update_label_text = None
    vertical_difference = None
    labelDetetcted_state = None
    # sbs_frame=None
    sbs_frame_L=None
    sbs_frame_R=None
    sbs_frame_with_detection=None
    tilt_motor_state=""
    finalDifference_y=None


    def __init__(self, var) -> None:
        self.var = var
        self.ai = AISettings()
        self.motor_settings = Motor()
        self.cam = Camera()
        self.motors = MotorParameters()


        self.pipeline = CameraStreamer()

        self.previous_difference = 0

        self.previous_error = 0
        self.total_error = 0

        self.set_pointt = self.ai.SET_POINT



    def newDetection(self):

        confidenceThreshold = 0.5
        # crop_height = 400
        # crop_width  = 400

        crop_height = self.ai.CROP_WINDOW_HEIGHT
        crop_width = self.ai.CROP_WINDOW_WIDTH
                
        def object_detection(frame, classIds, confs, bbox, x, y):
            detections = []
            for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
                if classId == 1 :
                    x1 = box[0] + x
                    y1 = box[1] + y
                    x2 = box[0] + box[2] + x
                    y2 = box[1] + box[3] + y
                    cx, cy = (x1 + x2) // 2 , (y1 + y2) // 2
                    detections.append([x1, y1, x2, y2, cx, cy])

                    # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

                    # cv2.rectangle(frameL, (detectionsL[0], detectionsL[1]), (detectionsL[2], detectionsL[3]), (0, 255, 0), 2)
            return frame, detections


        def orb_sim(frameL, frameR):
            orb = cv2.ORB_create()
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

            kpL, dpL = orb.detectAndCompute(frameL, None)
            kpR, dpR = orb.detectAndCompute(frameR, None)

            if dpL is None or dpR is None:
                return 0.0, None

            matches = bf.match(dpL, dpR)
            matches = sorted(matches, key=lambda x: x.distance)

            similar_regions = [i for i in matches if i.distance < 50]

            img_matches = cv2.drawMatches(frameL, kpL, frameR, kpR, matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

            if len(matches) > 0:
                return len(similar_regions) / len(matches), img_matches
            else:
                return 0.0, img_matches
            

        if self.var.frame_update is not None:
            

            frame = self.var.frame_update

            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

            # cv2.imshow("hhhh", frame)


            height, width = frame.shape[:2]

            # Step 3: Split the image into two parts vertically using NumPy slicing
            split_position = width // 2
            frameL = frame[:, :split_position]
            frameR = frame[:, split_position:]

                
            frame_height, frame_width, _ = frameL.shape

            y_start = int((frame_height/2) - (crop_height/2))
            y_end   = int((frame_height/2) + (crop_height/2))
            x_start = int((frame_width/2)  - (crop_width/2))
            x_end   = int((frame_width/2)  + (crop_width/2))

            cv2.rectangle(frameL, (x_start,y_start), (x_end,y_end), (0,0,0), 2)
            cv2.rectangle(frameR, (x_start,y_start), (x_end,y_end), (0,0,0), 2)

            cropL = frameL [y_start:y_end, x_start:x_end]
            cropR = frameR [y_start:y_end, x_start:x_end]

            classIdsL, confsL, bboxL = net.detect(cropL, confThreshold=confidenceThreshold)
            classIdsR, confsR, bboxR = net.detect(cropR, confThreshold=confidenceThreshold)

            self.labelDetetcted_state = False


            if len(classIdsL) > 0 and len(classIdsR) > 0:
                frameL, detectionsL = object_detection(frameL, classIdsL, confsL, bboxL, x_start, y_start)
                frameR, detectionsR = object_detection(frameR, classIdsR, confsR, bboxR, x_start, y_start)

                if len(detectionsL) > 0 and len(detectionsR) > 0:
                    detectionsL = detectionsL[0]
                    detectionsR = detectionsR[0]

                    cv2.rectangle(frameL, (detectionsL[0], detectionsL[1]), (detectionsL[2], detectionsL[3]), (0, 0, 255), 2)
                    cv2.rectangle(frameR, (detectionsR[0], detectionsR[1]), (detectionsR[2], detectionsR[3]), (0, 0, 255), 2)

                    objectL = cv2.cvtColor((frameL [detectionsL[1] : detectionsL[3], detectionsL[0] : detectionsL[2]]), cv2.COLOR_BGR2GRAY)
                    objectR = cv2.cvtColor((frameR [detectionsR[1] : detectionsR[3], detectionsR[0] : detectionsR[2]]), cv2.COLOR_BGR2GRAY)

                    orb_similarity, combine = orb_sim(objectL, objectR)

                    if orb_similarity > 0.3:
                        # print('Similarity using ORB is : ', orb_similarity)
                        # cv2.imshow('frame combine', combine)

                        # self.labelDetetctedMsg_Text = "Human Detected"
                        self.labelDetetcted_state = True

                        cv2.rectangle(frameL, (detectionsL[0], detectionsL[1]), (detectionsL[2], detectionsL[3]), (0, 255, 0), 2)
                        cv2.putText(frameL, 'PERSON', (detectionsL[0], detectionsL[1] -10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.circle(frameL, (detectionsL[4], detectionsL[5]), 5, (0, 0, 255), -1)

                        cv2.rectangle(frameR, (detectionsR[0], detectionsR[1]), (detectionsR[2], detectionsR[3]), (0, 255, 0), 2)
                        cv2.putText(frameR, 'PERSON', (detectionsR[0], detectionsR[1] -10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.circle(frameR, (detectionsR[4], detectionsR[5]), 5, (0, 0, 255), -1)

                        x1_diff = (int(detectionsL[0] - detectionsR[0]))
                        x2_diff = (int(detectionsL[2] - detectionsR[2]))
                        cx_diff = (int(detectionsL[4] - detectionsR[4]))

                        y1_diff = int(detectionsL[1] - detectionsR[1])
                        y2_diff = int(detectionsL[3] - detectionsR[3])
                        cy_diff = int(detectionsL[5] - detectionsR[5])



                        x_difference = [x1_diff, x2_diff, cx_diff]
                        y_difference = [y1_diff, y2_diff, cy_diff]
                        
                        dfx = pd.Series(np.array(x_difference))
                        dfy = pd.Series(np.array(y_difference))

                        mod	= dfx.mode()
                        mod_y = dfy.mode()
                        difference = mod.median()
                        difference_y = mod_y.median()


                        cv2.putText(frameL, str(difference), (x_start, y_start - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

                        difference = int(float(difference))
                        difference_y = int(float(difference_y))

                        self.finalDifference = difference
                        self.finalDifference_y = difference_y

                        
                        

            # cv2.imshow('Object Detection Left', frameL)
            # cv2.imshow('Object Detection Right', frameR)

            sbs = cv2.hconcat([frameL, frameR])

            self.sbs_frame_with_detection = sbs




    def sendMotorCommand(self, diff):



        diff = int(diff)

        error = int(diff-self.set_pointt)

        control_motor_L = 3
        control_motor_R = 4

        Kp=0.9
        Ki=0.4
        Kd=0.01

        delta_error = error - self.previous_error

        pValue = Kp * error
        iValue = Ki * (delta_error)
        dValue = Kd * self.total_error
        
        pidValue = pValue + iValue + dValue
        pidValue = abs(int(pidValue))

        self.previous_error = error
        self.total_error = self.total_error + error
        nu_of_steps = pidValue

        dir = self.ai.HCALIB_DIRECTION

        # drive motors
        if error > 0:
            dir = not dir
            
        direction_L = not dir
        direction_R = dir
        
        # direction_R = (not dir) if self.motor_settings.DIR_INVERSE_CONVERGENCE else (dir)

        print(direction_L, direction_R, "LR")

        cmd_L = self.motors.move_steps(m1=control_motor_L, move=True, direction=direction_L, steps=nu_of_steps)
        cmd_R = self.motors.move_steps(m1=control_motor_R, move=True, direction=direction_R, steps=nu_of_steps)
        self.motors.sendSerialCommand(cmd=cmd_L)
        time.sleep(0.1)
        self.motors.sendSerialCommand(cmd=cmd_R)


    def verticalCalibration(self):


        if self.var.frame_update is not None :

            frame = self.var.frame_update.copy()

            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

            print(frame.shape, "sssssssssssssssssss")
            

            # self.labelViewer(frame=frame)
            height, width = frame.shape[:2]

            # Step 3: Split the image into two parts vertically using NumPy slicing
            split_position = width // 2
            image1 = frame[:, :split_position]
            image2 = frame[:, split_position:]

            # print(image1.shape, "image1 shape")

            diff = 0

            if self.cam.SOURCE_L == 0:
                diff = self.v_calibration(grayL=image1, grayR=image2)
            else:
                
                diff = self.v_calibration(grayL=image2, grayR=image1)


            diff = int(diff)

            self.vertical_difference = int(diff)


        else:
            print("no frames found to calibrate")




    def v_calibration(self, grayL, grayR):

        
        difference = []

        orb = cv2.ORB_create()
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING2, crossCheck=True)
        
        # crop center of frame
        crop_height = 200
        crop_width  = 200

        frame_width = int(self.ai.FRAME_WIDTH)
        frame_height = int(self.ai.FRAME_HEIGHT)

        # frame_height, frame_width = grayL.shape


        y_start = int((frame_height / 2) - (crop_height / 2))
        y_end   = int((frame_height / 2) + (crop_height / 2))
        x_start = int((frame_width / 2)  - (crop_width / 2))
        x_end   = int((frame_width / 2)  + (crop_width / 2))

        grayL_cropped = grayL[y_start : y_end, x_start : x_end]
        grayR_cropped = grayR[y_start : y_end, x_start : x_end]

        keypoints_1 , descriptor_1 = orb.detectAndCompute(grayL_cropped, None)
        keypoints_2 , descriptor_2 = orb.detectAndCompute(grayR_cropped, None)
        
        if descriptor_1 is not None and descriptor_2 is not None:

            matches = matcher.match(descriptor_1, descriptor_2)
            matches = sorted(matches, key=lambda x: x.distance , reverse=False)

            if matches is not None:

                points_differencees = []
                
                for match in matches:
                    src_pts = keypoints_1[match.queryIdx].pt
                    dst_pts = keypoints_2[match.trainIdx].pt

                    difference = src_pts[1] - dst_pts[1]
                    points_differencees.append(int(difference))

                def reject_outliers(data, m=1):
                    return data[abs(data - np.mean(data)) < m * np.std(data)]
                
                dfx = pd.Series(reject_outliers(np.array(points_differencees)))
                mod	= dfx.mode()
                difference = mod.median()


        return difference


    def caliculatePID(self):


        diff = self.vertical_difference

        if -1 < diff and diff < 1 :
            pass
        else:
            error = diff

            control_motor = 5

            Kp=0.75
            Ki=0.2
            Kd=0.01

            delta_error = error - self.previous_error

            pValue = Kp * error
            iValue = Ki * (delta_error)
            dValue = Kd * self.total_error
            
            pidValue = pValue + iValue + dValue
            pidValue = abs(int(pidValue))

            self.previous_error = error
            self.total_error = self.total_error + error
            nu_of_steps = pidValue



            # drive motors
            # direction = False
            # if diff > 0:
            #     direction = not direction

            dir = self.ai.VCALIB_DIRECTION

            if self.cam.SOURCE_L==0:

                direction=dir if (diff>0) else not dir

            else:

                direction=not dir if (diff>0) else dir

            cmd = self.motors.move_steps(m1=control_motor, move=True, direction=direction, steps=nu_of_steps)


            self.motors.sendSerialCommand(cmd=cmd)
