import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
from datetime import datetime
from controls.settings import Camera, CameraSettings, System
import sys
Gst.init(sys.argv)
import numpy as np
import cv2
import queue
# import multiprocessing
import time
from threading import Timer
import subprocess

from pymediainfo import MediaInfo
import json
from PyQt5.QtCore import *

# from workers.worker_difference import WorkerDifference
# from PyQt5.QtCore import QTimer

import mediapipe as mp

from controls.motor import MotorParameters

from simple_pid import PID
import statistics
import pandas as pd


# mpPoseL = mp.solutions.pose
# mpPoseR = mp.solutions.pose
# # mpDraw = mp.solutions.drawing_utils
# poseL = mpPoseL.Pose()
# poseR = mpPoseR.Pose()

# from multiprocessing import Process

# STREAM_KEY = None
# global STREAM_KEY
# class WorkerDifference(Process):

#     def __init__(self, q):
#         super().__init__()
#         self.q = q
    

#     def run(self):
#         while True:
#             print("run_diff")
#             time.sleep(1)
#             # if not self.q.empty():
#             #     # diff = self.q.get()
#             #     print("hhh")

#             # else: 
#             #     print("no values")



class CameraStreamer:

    # fragment=None
    
    def __init__(self,apply_shader:bool=False):
        # Gst.init(sys.argv)
        self.cam 			= Camera()
        self.sys            = System()
        self.camSettings = CameraSettings()
        self.motors = MotorParameters()

        self.apply_shader=apply_shader

        self.current_process = None

        self.RECORD_VIDEO_DROP_LOCATION = self.cam.DROP_LOCATION

        

        self.load_settings()
        self.width = 3840
        self.height = 2160
        self.fps = 30
        self.pipeline = None
        self.pipeline1 = None
        self.bus = None
        self.loop = None
        self.halfwidth = int(self.width/2)

        self.FHD_preview_width = 1920
        self.FHD_preview_height = 1080
        self.half_FHD_preview_width = int(self.FHD_preview_width/2)

        self.HD_preview_width = 1080
        self.HD_preview_height = 720
        self.half_HD_preview_width = int(self.HD_preview_width/2)

        self.formatAppsink = '{GRAY8}'


        quality = "4K"
        current_timestamp 	= datetime.now().strftime("%Y_%m_%d-%H%M%S")
        self.RECORDING_PATH = "{1}{2}_{0}.mp4".format(str(current_timestamp), str(self.cam.DROP_LOCATION.strip()), str(quality.strip()))

        self.camSelected = "Stich"

        self.SENSOR_MODE = 0 

 
        self.source()
        
        self.buildFragmentShaders()

        # Calibration process

        self.queue1 = queue.Queue(maxsize=1)
        self.queue_diff = queue.Queue(maxsize=2)

        self.previous_difference = 0

        self.previous_error = 0
        self.total_error = 0

        # self.multy_process_queue = multiprocessing.Queue()

        # self.process_difference = WorkerDifference(q=self.multy_process_queue)
        # self.process_difference.daemon = True
        # self.process_difference.start()

        self.correction_checker = True



    def testWhileLoop(self):
        n=1
        while True:
            print("working//////////////////")
            time.sleep(5)



    def buildFragmentShaders(self):

        
        # create fragment shader for pixel projection
        self.fragment = """ \"
                #version %d core

                in vec2 v_texcoord; 

                uniform sampler2D tex; 
                uniform float time; 
                uniform float width; 
                uniform float height; 
                
                float deg2rad(float deg){
                    return 0.0174533*deg; 
                } 

                float _FOVH=%0.1f; 
                float _FOVV=%0.1f; 

                vec2 equirectangular(vec2 texcoord) { 
                    
                    float x = texcoord.x; 
                    float y = texcoord.y; 
                    vec2 pfish = vec2(0,0); 
                    vec3 psph = vec3(0,0,0); 

                    float FOV = deg2rad(_FOVH); 
                    float FOV2 = deg2rad(_FOVV); 
                    float width = 1.0; 
                    float height = 1.0; 

                    float theta = FOV * (x / width - 0.5); 
                    float phi = FOV2 * (y / height - 0.5); 
                    
                    psph.x = cos(phi)* sin(theta); 
                    psph.y = cos(phi) * cos(theta); 
                    psph.z = sin(phi); 
                    
                    theta = atan(psph.z,psph.x); 
                    phi = atan(sqrt(psph.x*psph.x+psph.z*psph.z),psph.y); 
                    
                    float r = width * phi / FOV; 
                    float r2 = height * phi / FOV2; 
                    
                    pfish.x = 0.5 * width + r * cos(theta); 
                    pfish.y = 0.5 * height + r2 * sin(theta); 
                    
                    return pfish;                                 
                } 

                out vec4 fragColor;
             
                void main () { 
                    fragColor = texture2D( tex, equirectangular(v_texcoord)); 
                }
                \" """ % (  450
                          , self.cam.HFOV,
                             self.cam.VFOV
                           )
        
        
        # shader for stitched frames
        self.fragment_double_frame = """ \"
                #version %d core

                in vec2 v_texcoord; 

                uniform sampler2D tex; 
                uniform float time; 
                uniform float width; 
                uniform float height; 
                
                float deg2rad(float deg){ 
                    return 0.0174533*deg; 
                } 
                
                float _FOVH=%0.1f; 
                float _FOVV=%0.1f;
                
                vec2 equirectangular(vec2 texcoord){ 
                    float x = texcoord.x; 
                    float y = texcoord.y; 
                    vec2 pfish = vec2(0,0); 
                    vec3 psph = vec3(0,0,0);
                    
                    float FOV = deg2rad(_FOVH); 
                    float FOV2 = deg2rad(_FOVV); 
                    float width = 1.0; 
                    float height = 1.0; 
                    float theta = FOV * (x / width - 0.5); 
                    float phi = FOV2 * (y / height - 0.5); 
                    
                    psph.x = cos(phi) * sin(theta); 
                    psph.y = cos(phi) * cos(theta); 
                    psph.z = sin(phi); 
                    
                    theta = atan(psph.z,psph.x); 
                    phi = atan(sqrt(psph.x*psph.x+psph.z*psph.z),psph.y); 
                    float r = width * phi / FOV; float r2 = height * phi / FOV2; pfish.x = 0.5 * width + r * cos(theta); 
                    pfish.y = 0.5 * height + r2 * sin(theta); return pfish; 
                } 
                
                out vec4 fragColor;

                void main () { 
                    vec2 projection = vec2(v_texcoord.x, v_texcoord.y); 
                    float isZero = floor(projection.x + 0.5);  
                    projection.x -= (0.5*isZero);  
                    projection.x *= 2.0; 
                    projection = equirectangular(projection); 
                    
                    projection.x *= 0.5; projection.x += (0.5*isZero);  

                    fragColor = texture2D( tex,  projection ); 
                }
            \" """ % (  450
                          , self.cam.HFOV,
                             self.cam.VFOV
                           )
        

        # self.fragment = self.fragment.strip().format(FOVH=self.FOVH, FOVV=self.FOVV)
        # print(self.fragment)

        # return self.fragment        



    def load_settings(self):

        # Argus Camera Properties
        self.WBMODE = self.camSettings.WBMODE
        self.AEANTI_BANDING = self.camSettings.AEANTI_BANDING
        self.EDGE_ENHANCE = self.camSettings.EDGE_ENHANCE
        self.AWB_LOCK = self.camSettings.AWB_LOCK
        self.AE_LOCK = self.camSettings.AE_LOCK
        self.EXPOSURE_COMPENSATION = self.camSettings.EXPOSURE_COMPENSATION
        self.SATURATION = self.camSettings.SATURATION
        self.TNR_MODE = self.camSettings.TNR_MODE
    

    def source(self):

        self.source_1 = f'''
        nvarguscamerasrc sensor-id              = {self.cam.SOURCE_L}
                        wbmode                  = {self.WBMODE} 
                        aeantibanding           = {self.AEANTI_BANDING} 
                        ee-mode                 = {self.EDGE_ENHANCE} 
                        awblock                 = {self.AWB_LOCK} 
                        aelock                  = {self.AE_LOCK} 
                        exposurecompensation    = {self.EXPOSURE_COMPENSATION} 
                        saturation              = {self.SATURATION}
                        tnr-mode                = {self.TNR_MODE}
                        name                    = source1 
                        do-timestamp            = 1
        '''

        self.source_2 = f'''
        nvarguscamerasrc sensor-id              = {self.cam.SOURCE_R}
                        wbmode                  = {self.WBMODE} 
                        aeantibanding           = {self.AEANTI_BANDING} 
                        ee-mode                 = {self.EDGE_ENHANCE} 
                        awblock                 = {self.AWB_LOCK} 
                        aelock                  = {self.AE_LOCK} 
                        exposurecompensation    = {self.EXPOSURE_COMPENSATION} 
                        saturation              = {self.SATURATION}
                        tnr-mode                = {self.TNR_MODE}
                        name                    = source2
                        do-timestamp            = 1
        '''


    # PREVIEW 01
    def leftCameraPreview(self, set_hw:bool=False, width:int=3840, height:int=2160, fps:int=30):

        self.current_process = "preview"

        self.camSelected = "Left"

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        comp_width = int((width - (self.cam.CROP_WIDTH)*2))
        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))

        source = f"{self.source_1}! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)RGBA "
        if self.apply_shader:
            source = f"{self.source_1}! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! queue2 ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)RGBA "

        self.DEFAULT_PIPELINE   = f"{source} ! queue2 ! nv3dsink sync=0 async=0 "
        
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()


    # PREVIEW 02
    def rightCameraPreview(self, set_hw:bool=False, width:int=3840, height:int=2160, fps:int=30):

        self.current_process = "preview"

        self.camSelected = "Right"

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        comp_width = int((width - (self.cam.CROP_WIDTH)*2))
        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))

        
        source = f"{self.source_2}! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)RGBA "
        if self.apply_shader:
            source = f"{self.source_2}! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! queue ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)RGBA "

        self.DEFAULT_PIPELINE   = f"{source} ! queue2 ! nv3dsink sync=0 async=0 "
        
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()

    def changeLR(self):
        
        print("hhhhh")

        source1 = self.pipeline.get_by_name("source1")
        source2 = self.pipeline.get_by_name("source2")

        source1.set_property("sensor-id", 1)
        source2.set_property("sensor-id", 0)

        print("jjjj")

        
    # PREVIEW 03
    def stichCameraPreview(self, set_hw:bool=False, width:int=3840, height:int=2160, fps:int=30):

        self.current_process = "preview"

        self.camSelected = "Stich"

        sensor_mode = 0
        # fisheye:  		FOVH -185 , FOVV - 130

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        comp_width = int((width - (self.cam.CROP_WIDTH)*2))
        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
        
        comp_width = comp_width if self.cam.h265_full_width else int(comp_width/2)

        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "

        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "
        

        self.DEFAULT_PIPELINE   = f"""
                    nvcompositor name=comp force-sync=1 clocksync=1 
                         sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                         sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! nv3dsink sync=0 async=0
                    {source_l} ! comp.
                    {source_r} ! comp.
                        """
        
        # print(self.DEFAULT_PIPELINE)

        self.playPipeline()


        # t0.! queue2 ! nvvidconv ! queue2 ! video/x-raw, format=(string)RGBA ! queue leaky=1 ! appsink name=appsink drop=true emit-signals=true caps="video/x-raw, format=(string)RGBA" max-buffers=1 
        # t0. ! queue2 ! nvvidconv ! video/x-raw ! jpegenc ! multifilesink location="image.jpg

    def startCorrection(self):
        

        if self.correction_checker==True:
            self.appsink = self.pipeline.get_by_name("appsink")
            
            self.appsink.connect("new-sample", self.startPushBufferstoQueue)
            print("wwww")
        else:
            self.appsink.disconnect_by_func(self.startPushBufferstoQueue)

        self.correction_checker = not self.correction_checker
        # self.correction_checker = not self.correction_checker


    def stopCorrection(self):

        self.appsink.disconnect_by_func(self.startPushBufferstoQueue)

        # self.correction_checker = False


    def caliculatePID(self, diff):

        error = diff
        # print("difference", diff)
        control_motor = 5

        if self.cam.SOURCE_L==0 and self.cam.SOURCE_R==1:
            pos_direction = 1
            neg_direction = 0

        if self.cam.SOURCE_L==1 and self.cam.SOURCE_R==0:
            pos_direction = 0
            neg_direction = 1

        Kp=0.2
        Ki=0.2
        Kd=0.01

        delta_error = error - self.previous_error

        pValue = Kp * error
        iValue = Ki * (delta_error)
        dValue = Kd * self.total_error
        
        pidValue = pValue + iValue + dValue
        pidValue = abs(int(pidValue))
        print("pidValue", pidValue)
        self.previous_error = error
        self.total_error = self.total_error + error
        nu_of_steps = pidValue

        print("nu-of-steps", nu_of_steps)

        # if self.correction_checker==True:

        if diff > 0:

            # nu_of_steps = 5

            cmd = self.motors.move_steps(m1=control_motor, move=True, direction=pos_direction, steps=nu_of_steps)
            self.motors.sendSerialCommand(cmd=cmd)
            pass
        elif diff < 0:

            # nu_of_steps = 5

            cmd = self.motors.move_steps(m1=control_motor, move=True, direction=neg_direction, steps=nu_of_steps)
            self.motors.sendSerialCommand(cmd=cmd)
        else:
            pass
        
    pass



    # PREVIEW 03
    def calibrationPreview(self, set_hw:bool=False, fps:int=2):
        
        appsink_frequency = 2
        appsink_frequency = int(1000000000 * appsink_frequency)

        self.v_calibration_width = 1920
        self.v_calibration_height = 1080

        width  =  1920
        height =  1080

        self.current_process = "calib"

        sensor_mode = 0
        # fisheye:  		FOVH -185 , FOVV - 130

        comp_width = int(width/2)
        comp_height= height

        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420 "
        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420 "
            
        self.DEFAULT_PIPELINE   = f"""
                    nvcompositor name=comp clocksync=1
                        sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0 
                                t0.! queue2 ! nvvidconv ! queue2 ! video/x-raw, format=(string)RGBA ! queue leaky=1 ! appsink name=appsink drop=true emit-signals=true caps="video/x-raw, format=(string)RGBA" max-buffers=1 throttle-time={appsink_frequency}
                    {source_l} ! queue2 ! comp.
                    {source_r} ! queue2 ! comp.
                """

        
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()

        elements='''
        throttle-time=1000000000
        caps="video/x-raw, format=(string)RGBA"
        nvvidconv ! video/x-raw(memory:NVMM), format=(string)RGBA
        queue2 use-buffering=true
        video/x-raw(memory:NVMM), width=(int)500, height=(int)500
        '''

    def startAppsinkProcess(self):
        
        self.appsink = self.pipeline.get_by_name("appsink")
        self.appsink.connect("new-sample", self.startPushBufferstoQueue)
        
        pass

    def startPushBufferstoQueue__(self, appsink):

        path = 'images/image1.jpg'
        image = cv2.imread(path)
        print(image.shape)


    def startPushBufferstoQueue(self, appsink):
        print("tttttttttttttttttt")

        sample = appsink.get_property("last-sample")

        if sample is not None:
            # get the buffer from the sample
            
            buffer = sample.get_buffer()

            data = buffer.extract_dup(0, buffer.get_size())

            # data = buffer.(0, buffer.get_size()
            
            caps = sample.get_caps()
            print(caps, "cap")
            sink_format = caps.get_structure(0).get_value('format')
            sink_height = caps.get_structure(0).get_value('height')
            sink_width  = caps.get_structure(0).get_value('width')

            print(sink_height, sink_width , sink_format)
            print("data shape", type(data))
            
            arry = np.ndarray(shape=(sink_height, sink_width, 4), buffer=data, dtype=np.uint8)
            print("yyyyyyyyyyyyyyyy")
            arry = cv2.cvtColor(arry, cv2.COLOR_RGBA2GRAY)
            
            # arry = cv2.cvtColor(arry, cv2.COLOR_BGRA2BGR)

            height, width = arry.shape
            half_width = int(width/2)
            
            part1=arry[0:height, 0:half_width]
            part2=arry[0:height, half_width:width]

            processed = self.vertical_correction(grayL=part1, grayR=part2)

            # process frames over
            # processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGRA)
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2BGRA)

            if self.queue1.full():
                self.queue1.get()


            self.queue1.put(processed)


    def vertical_correction(self, grayL, grayR):

        orb = cv2.ORB_create()
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING2, crossCheck=True)

        # crop center are for get feature points
        crop_height = 400
        crop_width  = 400

        size=grayL.shape
        frame_height = size[0]
        frame_width = size[1]

        y_start = int((frame_height/2)-(crop_height/2))
        y_end = int((frame_height/2)+(crop_height/2))

        x_start = int((frame_width/2)-(crop_width/2))
        x_end = int((frame_width/2)+(crop_width/2))

        grayL_cropped = grayL[y_start:y_end, x_start:x_end]
        grayR_cropped = grayR[y_start:y_end, x_start:x_end]

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

                print('pandas difference', difference)

                # # Write the difference to a file
                # file_path = "diff.txt"  # Provide the desired file path and name
                # with open(file_path, "a") as file:
                #     file.write(str(difference) + "\n")

                ################## change the keypoint positions ##################
                shift_x = x_start
                shift_y = y_start

                for i in range(len(keypoints_1)):
                    keypoints_1[i].pt = (keypoints_1[i].pt[0] + shift_x, keypoints_1[i].pt[1] + shift_y)

                for i in range(len(keypoints_2)):
                    keypoints_2[i].pt = (keypoints_2[i].pt[0] + shift_x, keypoints_2[i].pt[1] + shift_y)

                frameL=cv2.cvtColor(grayL, cv2.COLOR_GRAY2BGR)
                frameR=cv2.cvtColor(grayR, cv2.COLOR_GRAY2BGR)

                cv2.rectangle(grayL, (x_start,y_start), (x_end,y_end), (255,0,0), 2)
                cv2.rectangle(grayR, (x_start,y_start), (x_end,y_end), (255,0,0), 2)

                img_matches = cv2.drawMatches( frameL, keypoints_1, frameR, keypoints_2, matches[:50], None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,)
                            
                cv2.putText(img_matches, str(difference), (10, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2,)
            
                self.caliculatePID(diff=difference)

            else:
                img_matches = cv2.hconcat([grayL, grayR])
        else:
            img_matches = cv2.hconcat([grayL, grayR])

        return img_matches



    def startPreview(self):

        self.current_process = "calib"

        # db_width = int(640*2)
        width = self.v_calibration_width
        height = self.v_calibration_height

        fps=1

        self.pipe = f"""
                appsrc name=source is-live=true block=true format="bytes" stream-type=0 
                caps=video/x-raw,format=(string)RGBA,width=(int){width},height=(int){height},framerate=(fraction){fps}/1 
                ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)RGBA
                ! queue2 ! nvegltransform ! nveglglessink
                """
        
        self.view_pipeline = Gst.parse_launch(self.pipe)

        self.appsrc=self.view_pipeline.get_by_name('source')
        self.appsrc.connect('need-data', self.on_need_data)

        self.view_pipeline.set_state(Gst.State.READY)
        self.view_pipeline.set_state(Gst.State.PLAYING)



    def on_need_data(self, src, lenth):


        array = self.queue1.get() 
        data_bytes = array.tobytes()
        buffer = Gst.Buffer.new_wrapped(data_bytes)
        retval = src.emit('push-buffer', buffer)

        if retval != Gst.FlowReturn.OK:
            print(retval)
        return True
    


    def streamStartedAction(self):

        print("pipeline started")

        if self.current_process=='calib':
            self.startAppsinkProcess()
            self.startPreview()
            pass

        if self.current_process=='x_calib':
            self.startAppsinkProcess_x()
            self.startPreview_x()
            pass



    def blendPrevw(self):


        element_mqueue = Gst.ElementFactory.make("multiqueue", "mqueue")
        element_mqueue.set_property("max-size-buffers", 1)

        element_mix = Gst.ElementFactory.make("glstereomix", "mix")
        element_mix.set_property("multiview-mode", "checkerboard")

        element_gldownload = Gst.ElementFactory.make("gldownload")

        element_queue2 = Gst.ElementFactory.make("queue2")

        element_nvvidconv = Gst.ElementFactory.make("nvvidconv")
        element_nvvidconv.set_property("compute-hw", 1)

        element_nv3dsink = Gst.ElementFactory.make("nv3dsink")
        element_nv3dsink.set_property("sync", 0)



        element_source1 = Gst.ElementFactory.make("nvarguscamerasrc", "source1")
        element_source1.set_property("sensor-id", 0)
        element_source1.set_property("sensor-mode", 3)
        
                                     


        element_source2 = Gst.ElementFactory.make("nvarguscamerasrc", "source2")
        element_source2.set_property("sensor-id", 1)
        element_source1.set_property("sensor-mode", 3)


        source1_caps_1 = Gst.ElementFactory.make("capsfilter")
        source1_caps_1.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), width=(int)1296, height=(int)732, format=(string)NV12, framerate=(fraction)10/1"))

        element_tee1 = Gst.ElementFactory.make("tee", "t1")
        element_queue2 = Gst.ElementFactory.make("queue2")

        element_tee2 = Gst.ElementFactory.make("tee", "t2")

        element_nvjpegenc1 = Gst.ElementFactory.make("nvjpegenc")
        element_nvjpegenc2 = Gst.ElementFactory.make("nvjpegenc")

        element_multifilesink1 = Gst.ElementFactory.make("multifilesink")
        element_multifilesink1.set_property("location", "images/image1.jpg")
        element_multifilesink1.set_property("throttle-time", 500000000)
        element_multifilesink1.set_property("sync", 1)
        element_multifilesink1.set_property("async", 0)

        element_multifilesink2 = Gst.ElementFactory.make("multifilesink")
        element_multifilesink2.set_property("location", "images/image2.jpg")
        element_multifilesink2.set_property("throttle-time", 500000000)
        element_multifilesink2.set_property("sync", 1)
        element_multifilesink2.set_property("async", 0)

        # Create the pipeline
        pipeline = Gst.Pipeline.new("my-pipeline")

        # Add elements to the pipeline
        pipeline.add(element_mqueue)
        pipeline.add(element_mix)
        pipeline.add(element_gldownload)
        pipeline.add(element_queue2)
        pipeline.add(element_nvvidconv)
        pipeline.add(element_nv3dsink)
        pipeline.add(element_source1)
        pipeline.add(element_source2)
        pipeline.add(element_tee1)
        pipeline.add(element_tee2)
        pipeline.add(element_nvjpegenc1)
        pipeline.add(element_nvjpegenc2)
        pipeline.add(element_multifilesink1)
        pipeline.add(element_multifilesink2)

        # Link elements together
        element_mix.link(element_queue2)
        element_queue2.link(element_gldownload)
        element_gldownload.link(element_nvvidconv)
        element_nvvidconv.link(element_nv3dsink)
        element_source1.link(element_tee1)
        element_source2.link(element_tee2)
        element_tee1.link(element_queue2)
        element_tee2.link(element_queue2)
        element_queue2.link(element_nvvidconv)
        element_nvvidconv.link(element_nvjpegenc1)
        element_nvjpegenc1.link(element_multifilesink1)
        element_nvjpegenc2.link(element_multifilesink2)

        # Start the pipeline
        # pipeline   = Gst.parse_launch(self.DEFAULT_PIPELINE)
        # self.bus        = self.pipeline.get_bus()
        # self.bus.add_signal_watch()
        pipeline.set_state(Gst.State.PLAYING)
        # self.loop       = GLib.MainLoop()
        # self.bus.connect("message", self.on_message, self.loop)
        # self.loop.run()



        # ... Perform further processing or wait for a certain duration ...

        # Stop the pipeline
        # pipeline.set_state(Gst.State.NULL)


    # FRANK CREATED TO REPALCE 3 FUNCTIONS
    def preview_3D__(self, set_hw:bool=False, fps:int=10, quality:str="2160p", mode:str="sbs"):
        if (quality=="720p"):
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  += 8
            self.cam.CROP_HEIGHT += 6

            sensor_mode = 3
            fps         = 70

        elif(quality=="1080p"):
            width       = 1944   #1920 + 24
            height      = 1096   #1080 + 16

            self.cam.CROP_WIDTH  += 12
            self.cam.CROP_HEIGHT += 8

            sensor_mode = 2
            fps         = 60

        else:
            width       = 3840
            height      = 2160

            sensor_mode = 1
            fps         = 40

        # fisheye:  FOVH-185, FOVV-130

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        comp_width = int((width - (self.cam.CROP_WIDTH)*2))
        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
        
        comp_width = comp_width if (self.cam.h265_full_width or quality != "2160p") else int(comp_width/2)

        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! tee name=t1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! tee name=t1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "

        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! tee name=t2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! tee name=t2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "
        
        self.DEFAULT_PIPELINE   = f"""
                    multiqueue max-size-buffers=1 name=mqueue 
                    nvcompositor name=comp force-sync=1 clocksync=1 
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! queue2 ! nv3dsink sync=0 async=0
                    {source_l} ! queue2 ! mqueue.sink_1 mqueue.src_1 ! comp.sink_0
                    {source_r} ! queue2 ! mqueue.sink_2 mqueue.src_2 ! comp.sink_1
                        t1. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image1.jpg" throttle-time=500000000 sync=1 async=0 
                        t2. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0 
                """
        self.playPipeline()


    def preview_3D(self, set_hw:bool=False, fps:int=10, quality:str="2160p", mode:str="mono"):
        self.current_process = "preview"
        self.camSelected = "Stich"


        if(quality=="1080p"):

            width      = 1944   #1920 + 24
            height     = 1096   #1080 + 16
            
            self.cam.CROP_WIDTH  = 12
            self.cam.CROP_HEIGHT = 8

            sensor_mode= 2

        else: #don't use 2160p in this
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  = 8
            self.cam.CROP_HEIGHT = 6

            sensor_mode= 3

        # fisheye:  		FOVH -185 , FOVV - 130

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        shader_fix = f"glupload"
        if self.apply_shader:
            shader_fix = f"videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment}"


        self.DEFAULT_PIPELINE  = f'''
                    glstereomix clock-sync=1 name=mix downmix-mode=0 ! video/x-raw(memory:GLMemory), multiview-mode={mode} ! 
                        gldownload ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM) ! nv3dsink sync=0 
                    {self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! queue2 ! tee name=t1 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                    {self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! queue2 ! tee name=t2 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                        t1. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image1.jpg" throttle-time=500000000 sync=1 async=0 
                        t2. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0 
                '''
        
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()
    
    # PREVIEW 04 
    def blend_Preview(self, set_hw:bool=False, fps:int=10, quality:str="720p"):


        self.current_process = "preview"

        self.camSelected = "Stich"


        if(quality=="1080p"):

            width      = 1944   #1920 + 24
            height     = 1096   #1080 + 16

            # width      = 3864   #1920 + 24
            # height     = 2176   #1080 + 16
            
            self.cam.CROP_WIDTH  += 12
            self.cam.CROP_HEIGHT += 8

            sensor_mode= 2

        else:
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  += 8
            self.cam.CROP_HEIGHT += 6

            sensor_mode= 3

        # fisheye:  		FOVH -185 , FOVV - 130

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        shader_fix = f"glupload"
        if self.apply_shader:
            shader_fix = f"videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment}"


        self.DEFAULT_PIPELINE  = f'''
                    multiqueue max-size-buffers=1 name=mqueue
                    glstereomix name=mix ! video/x-raw(memory:GLMemory), multiview-mode=checkerboard ! 
                        gldownload ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM) ! nv3dsink sync=0 
                    {self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! mqueue.sink_1 mqueue.src_1 ! tee name=t1 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                    {self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! mqueue.sink_2 mqueue.src_2 ! tee name=t2 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                        t1. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image1.jpg" throttle-time=500000000 sync=1 async=0 
                        t2. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0 
                '''
        
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()

    # PREVIEW 04 
    def sideBysise_Preview(self, set_hw:bool=False, fps:int=10, quality:str="720p"):


        self.current_process = "preview"

        self.camSelected = "Stich"


        if(quality=="1080p"):

            width      = 1944   #1920 + 24
            height     = 1096   #1080 + 16

            # width      = 3864   #1920 + 24
            # height     = 2176   #1080 + 16
            
            self.cam.CROP_WIDTH  = 12
            self.cam.CROP_HEIGHT = 8

            sensor_mode= 2

        else:
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  = 8
            self.cam.CROP_HEIGHT = 6

            sensor_mode= 3

        # fisheye:  		FOVH -185 , FOVV - 130

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        shader_fix = f"glupload"
        if self.apply_shader:
            shader_fix = f"videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment}"


        self.DEFAULT_PIPELINE  = f'''
                    glstereomix name=mix ! capsfilter name=caps01 caps="video/x-raw(memory:GLMemory), multiview-mode=side-by-side" ! 
                        gldownload ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM) ! nv3dsink sync=0 
                    {self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! tee name=t1 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                    {self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! tee name=t2 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                        t1. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image1.jpg" throttle-time=500000000 sync=1 async=0 
                        t2. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0 
                '''
        
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()

    # PREVIEW 04 
    def mono_Preview(self, set_hw:bool=False, fps:int=10, quality:str="720p"):


        self.current_process = "preview"

        self.camSelected = "Stich"


        if(quality=="1080p"):

            width      = 1944   #1920 + 24
            height     = 1096   #1080 + 16

            # width      = 3864   #1920 + 24
            # height     = 2176   #1080 + 16
            
            # ignoring crop paramms on yaml
            self.cam.CROP_WIDTH  = 12
            self.cam.CROP_HEIGHT = 8

            sensor_mode= 2

        else:
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  = 8
            self.cam.CROP_HEIGHT = 6

            sensor_mode= 3

        # fisheye:  		FOVH -185 , FOVV - 130

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        shader_fix = f"glupload"
        if self.apply_shader:
            shader_fix = f"videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment}"


        self.DEFAULT_PIPELINE  = f'''
                    multiqueue max-size-buffers=1 name=mqueue
                    glstereomix name=mix ! capsfilter name=caps01 caps="video/x-raw(memory:GLMemory), multiview-mode=mono" ! 
                        gldownload ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM) ! nv3dsink sync=0 
                    {self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! mqueue.sink_1 mqueue.src_1 ! tee name=t1 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                    {self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! mqueue.sink_2 mqueue.src_2 ! tee name=t2 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                        t1. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image1.jpg" throttle-time=500000000 sync=1 async=0 
                        t2. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0 
                '''
        
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()

    # PREVIEW 04 
    def blendCameraPreview(self, set_hw:bool=False, fps:int=10, quality:str="720p"):


        self.current_process = "preview"

        self.camSelected = "Stich"


        if(quality=="1080p"):

            width      = 1944   #1920 + 24
            height     = 1096   #1080 + 16

            # width      = 3864   #1920 + 24
            # height     = 2176   #1080 + 16
            
            self.cam.CROP_WIDTH  = 12
            self.cam.CROP_HEIGHT = 8

            sensor_mode= 2

        else:
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  = 8
            self.cam.CROP_HEIGHT = 6

            sensor_mode= 3

        # fisheye:  		FOVH -185 , FOVV - 130

        # {
        #     mono, 
        #     left, 
        #     right, 
        #     side-by-side, 
        #     side-by-side-quincunx, 
        #     column-interleaved, 
        #     row-interleaved, 
        #     top-bottom, 
        #     checkerboard, 
        #     frame-by-frame, 
        #     multiview-frame-by-frame, 
        #     separated
        # }

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        shader_fix = f"glupload"
        if self.apply_shader:
            shader_fix = f"videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment}"

        # self.DEFAULT_PIPELINE45646   = f'''
        #             multiqueue max-size-buffers=1 name=mqueue
        #             glstereomix name=mix ! capsfilter name=caps01 caps=Gst.Caps.from_string("video/x-raw(memory:GLMemory), multiview-mode=side-by-side") ! 
        #              ! queue2 ! glimagesink output-multiview-mode=side-by-side
        #             {self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! mqueue.sink_1 mqueue.src_1 ! tee name=t1 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
        #             {self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! mqueue.sink_2 mqueue.src_2 ! tee name=t2 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
        #                 t1. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image1.jpg" throttle-time=500000000 sync=1 async=0 
        #                 t2. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0 
        #         '''

        self.DEFAULT_PIPELINE__  = f'''
                    multiqueue max-size-buffers=1 name=mqueue
                    glstereomix name=mix ! capsfilter name=caps01 caps="video/x-raw(memory:GLMemory), multiview-mode=row-interleaved" ! 
                        gldownload ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM) ! nv3dsink sync=0 
                    {self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! mqueue.sink_1 mqueue.src_1 ! tee name=t1 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                    {self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! mqueue.sink_2 mqueue.src_2 ! tee name=t2 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                        t1. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image1.jpg" throttle-time=500000000 sync=1 async=0 
                        t2. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0 
                '''

        self.DEFAULT_PIPELINE  = f'''
                    multiqueue max-size-buffers=1 name=mqueue
                    glstereomix name=mix ! capsfilter name=caps01 caps="video/x-raw(memory:GLMemory), multiview-mode=row-interleaved" ! 
                        gldownload ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM) ! nv3dsink sync=0 
                    {self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! mqueue.sink_1 mqueue.src_1 ! tee name=t1 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                    {self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! mqueue.sink_2 mqueue.src_2 ! tee name=t2 ! queue2 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! {shader_fix} ! mix. 
                        t1. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image1.jpg" throttle-time=500000000 sync=1 async=0 
                        t2. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0 
                '''

        # Gst.Caps.from_string("video/x-raw(memory:GLMemory), multiview-mode=side-by-side")
        
        # comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
        # comp_width = int((width - (self.cam.CROP_WIDTH)*2))

        # source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA "
        # if self.apply_shader:
        #     source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload "
        
        # source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA "
        # if self.apply_shader:
        #     source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload "
        

        # self.DEFAULT_PIPELINE = f'''
        #             multiqueue max-size-buffers=1 name=mqueue 
        #             nvcompositor name=comp background=black clocksync=1
        #                 sink_0::zorder=0 sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} sink_0::alpha=0.5
        #                 sink_1::zorder=1 sink_1::xpos=0 sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} sink_1::alpha=0.5 ! queue2 ! nv3dsink sync=0 async=0 
        #             {source_l} ! mqueue.sink_1 mqueue.src_1 ! tee name=t1 
        #             {source_r} ! mqueue.sink_2 mqueue.src_2 ! tee name=t2
        #             t1. ! queue2 ! nvvidconv ! comp.
        #             t2. ! queue2 ! nvvidconv ! comp.
        #             t1. ! queue2 ! nvvidconv ! nvjpegenc ! multifilesink location="images/image1.jpg" throttle-time=500000000 sync=1 async=0 
        #             t2. ! queue2 ! nvvidconv ! nvjpegenc ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0 
        #         '''
        
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()


        sample='''
            t0. ! queue2 ! video/x-raw, format=(string)NV12 ! jpegenc ! multifilesink location="/recordings/img_%06.jpg"
            nvvidconv ! queue2 ! nvjpegenc ! queue2 ! multifilesink sync=true next-file=3

            gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! "video/x-raw(memory:NVMM), format=(string)NV12, width=400, height=400, framerate=1/5" ! nvvidconv ! "video/x-raw" ! identity sync=true ! jpegenc ! multifilesink location="image.jpg"
            \
            
            video/x-raw, framerate=(fraction)1/1 

            t0. ! queue2 ! nvvidconv ! video/x-raw ! jpegenc ! multifilesink location="image.jpg

            t0. ! queue2 ! nvvidconv ! video/x-raw, framerate=(fraction)1/1 ! jpegenc ! multifilesink location="image.jpg"
           
            multifilesink location="images/image2-%05d.jpg" throttle-time=9000000000 sync=1 async=0
             '''

    def changeCaps(self):

        print("changing")
        capsfilter01 = self.pipeline.get_by_name("caps01")

        self.pipeline.set_state(Gst.State.PAUSED)
        print("changing_param")
        capsfilter01.set_property("caps", "video/x-raw(memory:GLMemory), multiview-mode=side-by-side")
        # capsfilter01.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:GLMemory), multiview-mode=side-by-side"))
        self.pipeline.set_state(Gst.State.PLAYING)
        print("changing_param_222")

    def stream_4k(self, stream_key:str="key", set_hw:bool=False, quality:str="1080p", fps:int=30, stream_type:str="web"):

        self.camSelected = "Stich"

        self.DEFAULT_PIPELINE   = f"""
                 nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM), width=(int)3840, height=(int)2160, format=(string)NV12, framerate=(fraction)30/1 ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420 ! nvv4l2h264enc qp-range="24,24:28,28:30,30" control-rate=0 ! video/x-h264, stream-format=(string)byte-stream ! h264parse ! video/x-h264,stream-format=avc ! kvssink access-key="AKIATIYI4YO7VA356I7G" secret-key="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" aws-region="ap-northeast-1" stream-name="GIOVIEW"
                """
        
        self.playPipeline()



    # STREAM RTMP
    def localStream2VR(self, fps:int=15, quality:str="1080p"):
        self.current_process = "streaming"

        self.camSelected = "Stich"

        if(quality=="1080p"):

            width      = 1944   #1920 + 24
            height     = 1096   #1080 + 16

            # width      = 3864   #1920 + 24
            # height     = 2176   #1080 + 16
            
            self.cam.CROP_WIDTH  += 12
            self.cam.CROP_HEIGHT += 8

            sensor_mode= 2

        else:
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  += 8
            self.cam.CROP_HEIGHT += 6

            sensor_mode= 3

        # fisheye:  		FOVH -185 , FOVV - 130


        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
        comp_width = int((width - (self.cam.CROP_WIDTH)*2) / 2)

        localhost = self.cam.VR_ADDRESS



        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 "
        
        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 "
        



        

        # sensor_mode = 0
        # width = 1920
        # height = 1080
        # comp_width = int(width/2)

        # localhost = self.cam.VR_ADDRESS


        # source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv "
        # if self.apply_shader:
        #     source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 "
        
        # source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv "
        # if self.apply_shader:
        #     source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 "
        
        self.DEFAULT_PIPELINE   = f"""
                    nvcompositor name=comp force-sync=1 clocksync=1 
                         sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                         sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! video/x-raw(memory:NVMM) ! nv3dsink sync=0 async=0 
                            t0. ! queue2 ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420
                            ! queue2 ! nvvidconv ! nvjpegenc ! rndbuffersize ! queue leaky=1 ! udpsink host={localhost} port=3001 sync=0 async=0 
                     {source_l} ! queue2 ! comp.
                    {source_r} ! queue2 ! comp.
                """
        
        print(self.DEFAULT_PIPELINE)
        self.playPipeline()
        
        sample='''
            		self.recbin 	= Gst.Bin.new("MASTER_BIN")
		
		self.enc 		= Gst.ElementFactory.make("nvjpegenc")
		self.udpsink 	= Gst.ElementFactory.make("udpsink")
		
		self.queue_0	= Gst.ElementFactory.make("queue2")
		self.convert 	= Gst.ElementFactory.make("nvvidconv")
		self.caps_video_1 = Gst.ElementFactory.make("capsfilter")
		self.queue_1	= Gst.ElementFactory.make("queue2")
		self.rndbuffer	= Gst.ElementFactory.make("rndbuffersize")
		self.queue_2	= Gst.ElementFactory.make("queue2")

gst-launch-1.0 -e nvcompositor name=comp 
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=1920 sink_0::height=2160 
sink_1::xpos=1920 sink_1::ypos=0 sink_1::width=1920 sink_1::height=2160 ! queue2 ! tee name=t0  
t0. ! queue2 ! videorate skip-to-first=1 ! "video/x-raw(memory:NVMM), framerate=(fraction)30/1" ! nv3dsink sync=0 async=0 
t0. ! queue2 ! videorate skip-to-first=1 ! "video/x-raw(memory:NVMM), framerate=(fraction)30/1" ! video/x-raw(memory:NVMM), format=(string)I420 !
queue2 ! nvvidconv ! nvjpegenc ! rndbuffersize max=65000 ! queue2 ! udpsink host=192.168.1.106 port=3001 sync=0 async=0
nvarguscamerasrc sensor-id=1 name=source1 sensor-mode=0 ! "video/x-raw(memory:NVMM), width=(int)3840, height=(int)2160, format=(string)NV12, framerate=(fraction)30/1"  ! nvvidconv  ! comp. 
nvarguscamerasrc sensor-id=0 name=source2 sensor-mode=0 ! "video/x-raw(memory:NVMM), width=(int)3840, height=(int)2160, format=(string)NV12, framerate=(fraction)30/1"  ! nvvidconv  ! comp. 
                




                '''


    # STREAM RTMP
    def stream_rtmp_4k(self, fps:int=30):

        self.camSelected = "Stich"

        self.current_process = "streaming"

        # url = 'rtmp://192.168.1.95/live/'
        # key = 'livestream'

        # url = 'rtmp://54.172.159.142:1935/test1/'
        # key = 'live1'

        # streamurl = f"{url}{key}"

        streamurl = f"{self.cam.STREAM_URL_4K}"

        # streamurl = 'rtmp://e9867802feb9.entrypoint.cloud.wowza.com/app-r6Ds7584/bbfa6967'

        sensor_mode = 0
        width = 3840
        height = 2160
        comp_width = int(width/2)


        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv "
        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv "
       

        self.DEFAULT_PIPELINE   = f"""
                    multiqueue max-size-buffers=1 name=mqueue 
                    nvcompositor name=comp force-sync=1 clocksync=1 
                         sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={height} 
                         sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! nv3dsink sync=0 async=0
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! 
                                    nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 ! queue2 ! nvv4l2h264enc
                                                    bitrate = {self.cam.H264_STREAM_4K_BITRATE}
                                                    insert-aud=1 
                                                    iframeinterval=30 
                                                    idrinterval=60 
                                                        ! h264parse ! flvmux name=mux streamable=1 ! queue2 ! rtmpsink location={streamurl} pulsesrc do-timestamp=1 provide-clock=false ! audio/x-raw ! queue2 ! audioconvert ! queue2 ! audioresample ! queue2 ! voaacenc bitrate=128000 ! queue2 ! mux.
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.
                    {source_r} ! mqueue.sink_2 mqueue.src_2 ! comp.
                """
        
        print(self.DEFAULT_PIPELINE)
        self.playPipeline()

    # STREAM RTMP
    def stream_rtmp(self, stream_key:str="key", set_hw:bool=False, quality:str="1080p", fps:int=30, stream_type:str="web"):

        self.camSelected = "Stich"

        self.current_process = "streaming"


        # url = 'rtmp://192.168.1.95/live/'
        # key = 'livestream'

        url = 'rtmp://54.172.159.142:1935/test1/'
        key = 'live1'

        if stream_type=="web":

            streamurl = f"{str(self.cam.CLOUD_URL_RTMP).strip()}{str(stream_key).strip()}"

        if stream_type=="local":

            streamurl = f"{url}{key}"




        if(quality=="1080p"):

            width      = 1944   #1920 + 24
            height     = 1096   #1080 + 16

            # width      = 3864   #1920 + 24
            # height     = 2176   #1080 + 16
            
            self.cam.CROP_WIDTH  += 12
            self.cam.CROP_HEIGHT += 8

            sensor_mode= 2

        else:
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  += 8
            self.cam.CROP_HEIGHT += 6

            sensor_mode= 3

        # fisheye:  		FOVH -185 , FOVV - 130


        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
        comp_width = int((width - (self.cam.CROP_WIDTH)*2) / 2)


        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 "
        
        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 "
        

        self.DEFAULT_PIPELINE   = f"""
                    multiqueue max-size-buffers=1 name=mqueue 
                    nvcompositor name=comp force-sync=1 clocksync=1 
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! nv3dsink sync=0 async=0
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! 
                                    nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 ! queue2 ! nvv4l2h264enc
                                                    qp-range={self.cam.QP_RANGE_STREAM}
                                                    bitrate={self.cam.H264_STREAM_BITRATE}
                                                    insert-aud=1 
                                                    iframeinterval=30 
                                                    idrinterval=60 
                                                        ! h264parse ! flvmux name=mux streamable=1 ! queue2 ! rtmpsink location={streamurl} pulsesrc do-timestamp=1 provide-clock=false ! audio/x-raw ! queue2 ! audioconvert ! queue2 ! audioresample ! queue2 ! voaacenc bitrate=128000 ! queue2 ! mux.
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.
                    {source_r} ! mqueue.sink_2 mqueue.src_2 ! comp.
                """
        
        if self.sys.SINGLE_CAM_OPERATION:
            self.DEFAULT_PIPELINE   = f"""
                    multiqueue max-size-buffers=1 name=mqueue 
                    nvcompositor name=comp 
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! nv3dsink sync=0 async=0
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! 
                                    nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 ! queue2 ! nvv4l2h264enc
                                                    qp-range={self.cam.QP_RANGE_STREAM} 
                                                    bitrate={self.cam.H264_STREAM_BITRATE} 
                                                    insert-aud=1 
                                                    iframeinterval=30 
                                                    idrinterval=60 
                                                        ! h264parse ! flvmux name=mux streamable=1 ! queue2 ! rtmpsink location={streamurl} pulsesrc do-timestamp=1 provide-clock=false ! audio/x-raw ! queue2 ! audioconvert ! queue2 ! audioresample ! queue2 ! voaacenc bitrate=128000 ! queue2 ! mux.
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.
                """
            
        # queue2 ! video/x-h264, stream-format=(string)byte-stream ! h264parse
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()

    # RECORD H264
    def record_h264(self, set_hw:bool=False, quality:str="2160p", fps:int=30, file_type:str="mp4", ):

        self.camSelected = "Stich"

        self.current_process = "recording_h264"

        if (quality=="720p"):
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  += 8
            self.cam.CROP_HEIGHT += 6

            sensor_mode= 3

            comp_width = int((width - (self.cam.CROP_WIDTH)*2))

        elif(quality=="1080p"):

            width      = 1944   #1920 + 24
            height     = 1096   #1080 + 16
            
            self.cam.CROP_WIDTH  += 12
            self.cam.CROP_HEIGHT += 8

            sensor_mode= 2

            comp_width = int((width - (self.cam.CROP_WIDTH)*2))

        else:
            width      = 3840
            height     = 2160

            sensor_mode= 1

            comp_width = int((width - (self.cam.CROP_WIDTH)*2)/2)
        # fisheye:  		FOVH -185 , FOVV - 130

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))


        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 "
        
        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 "
        
        rec_file_uri     = "{2}{3}_{0}.{1}".format(str(datetime.now().strftime("%H%M%S")), file_type, str(self.cam.DROP_LOCATION.strip()),("HD" if quality.strip() == "720p" else ("FHD" if quality.strip() == "1080p" else "UHD")))

        # select the muxing pattern
        mux = None

        if file_type == "mp4":
            mux = "qtmux"
        elif file_type == "mkv":
            mux = "matroskamux"
        else :
            print("WARNING!: ", "System supports [mp4 | mkv] extensions only")

        
        self.DEFAULT_PIPELINE   = f"""
                    multiqueue max-size-buffers=1 name=mqueue 
                    nvcompositor force-sync=1 name=comp 
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! nv3dsink sync=0 async=0
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! 
                                    nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 ! queue2 ! nvv4l2h264enc
                                                    bitrate={self.cam.H264_REC_BITRATE} 
                                                    peak-bitrate={self.cam.H264_REC_BITRATE}
                                                    control-rate=0
                                                    maxperf-enable=1
                                                    preset-level=2
                                                        ! h264parse ! {mux} name=mux ! filesink location={rec_file_uri} pulsesrc do-timestamp=1 provide-clock=false ! audio/x-raw ! queue2 ! audioconvert ! queue2 ! audioresample ! queue2 ! voaacenc bitrate=128000 ! queue2 ! mux.
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.
                    {source_r} ! mqueue.sink_2 mqueue.src_2 ! comp.
                    
                """
        
        if self.sys.SINGLE_CAM_OPERATION:
            self.DEFAULT_PIPELINE   = f"""
                    multiqueue max-size-buffers=1 name=mqueue 
                    nvcompositor name=comp 
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! nv3dsink sync=0 async=0
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! 
                                    nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 ! queue2 ! nvv4l2h264enc
                                                    bitrate={self.cam.H264_REC_BITRATE} 
                                                    peak-bitrate={self.cam.H264_REC_BITRATE}
                                                    control-rate=0
                                                    maxperf-enable=1
                                                    preset-level=2
                                                        ! h264parse ! {mux} name=mux ! filesink location={rec_file_uri} pulsesrc do-timestamp=1 provide-clock=false ! audio/x-raw ! queue2 ! audioconvert ! queue2 ! audioresample ! queue2 ! voaacenc bitrate=128000 ! queue2 ! mux.
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.
                """

        # print(self.DEFAULT_PIPELINE)

        self.playPipeline()

    # RECORD H265
    def record_h265(self, set_hw:bool=False, fps:int=30, quality:str="2160p", file_type:str="mp4"):

        self.camSelected = "Stich"

        self.current_process = "recording_h265"

        if (quality=="720p"):
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  += 8
            self.cam.CROP_HEIGHT += 6

            sensor_mode = 3
            fps         = 70

        elif(quality=="1080p"):
            width       = 1944   #1920 + 24
            height      = 1096   #1080 + 16

            self.cam.CROP_WIDTH  += 12
            self.cam.CROP_HEIGHT += 8

            sensor_mode = 2
            fps         = 60

        else:
            width       = 3840
            height      = 2160

            sensor_mode = 1
            fps         = 40

        # fisheye:  FOVH-185, FOVV-130

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        comp_width = int((width - (self.cam.CROP_WIDTH)*2))
        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
        
        comp_width = comp_width if (self.cam.h265_full_width or quality != "2160p") else int(comp_width/2)

        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "

        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "
        
        rec_file_uri     = "{2}{3}_{0}.{1}".format(str(datetime.now().strftime("%H%M%S")), file_type, str(self.RECORD_VIDEO_DROP_LOCATION.strip()),("HD" if quality.strip() == "720p" else ("FHD" if quality.strip() == "1080p" else "UHD")))

        # select the muxing pattern
        mux = None

        if file_type == "mp4":
            mux = "qtmux"
        elif file_type == "mkv":
            mux = "matroskamux"
        else :
            print("WARNING!: ", "System supports [mp4 | mkv] extensions only")

        
        self.DEFAULT_PIPELINE   = f"""
                    multiqueue max-size-buffers=1 sync-by-running-time=1 use-interleave=1 name=mqueue 
                    nvcompositor name=comp force-sync=1 clocksync=1 
                        sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! nv3dsink
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! 
                                    nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 ! queue2 use-buffering=1 max-size-buffers=500 ! nvv4l2h265enc
                                                    bitrate={self.cam.H265_REC_BITRATE} 
                                                    peak-bitrate={self.cam.H265_REC_BITRATE} 
                                                    control-rate=0 
                                                    maxperf-enable=1 ! h265parse ! queue2 ! {mux} name=mux ! queue2 ! filesink sync=1 async=0 location={rec_file_uri} pulsesrc do-timestamp=1 ! queue2 ! audio/x-raw ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! queue2 ! mux.
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.sink_0
                    {source_r} ! mqueue.sink_2 mqueue.src_2 ! comp.sink_1
                """
        

        if self.sys.SINGLE_CAM_OPERATION:
            self.DEFAULT_PIPELINE   = f"""
                    multiqueue max-size-buffers=1 name=mqueue 
                    nvcompositor name=comp clocksync=1 
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! nv3dsink sync=0 async=0
                                t0. ! queue2 ! videorate skip-to-first=1 ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! 
                                    nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 ! queue2 use-buffering=1 ! nvv4l2h265enc
                                                    bitrate={self.cam.H265_REC_BITRATE} 
                                                    peak-bitrate={self.cam.H265_REC_BITRATE}
                                                    control-rate=0
                                                    maxperf-enable=1 ! h265parse ! {mux} name=mux ! filesink sync=1 async=0 location={rec_file_uri} pulsesrc do-timestamp=1 provide-clock=false ! audio/x-raw ! queue2 ! audioconvert ! queue2 ! audioresample ! queue2 ! voaacenc bitrate=128000 ! queue2 ! mux.
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.
                """

        self.playPipeline()
   




    def get_media_info(self, source_file:str):
        media_info_dict = {}
        
        media_info = MediaInfo.parse(source_file.strip())

        # print(json.dumps(media_info.to_data()))

        for video_track in media_info.video_tracks:
            if video_track:
                media_info_dict = {
                    'track_type': video_track.track_type,
                    'format': video_track.format,
                    'internet_media_type': video_track.internet_media_type,
                    'codec_id': video_track.codec_id,
                    'duration': video_track.duration,
                    'bit_rate': video_track.bit_rate,
                    'maximum_bit_rate':video_track.maximum_bit_rate,
                    'width':video_track.width,
                    'height':video_track.height
                }

        return media_info_dict
    

    # APPLY FRAGMENT SHADER
    def post_process(self, set_hw:bool=False, source_file:str=None):
        self.camSelected = "play_video"

        source_file_uri     = "{0}{1}".format(str(self.cam.DROP_LOCATION.strip()), source_file.strip())
        sink_file_uri       = "{0}SH_{1}".format(str(self.cam.DROP_LOCATION.strip()), source_file.strip())

        media_info = self.get_media_info(source_file_uri)

        self.DEFAULT_PIPELINE = None

        if(str(media_info['internet_media_type']).upper() == 'VIDEO/H265'):
            self.DEFAULT_PIPELINE = f"""
                filesrc location={source_file_uri} ! 
                qtdemux ! queue ! h265parse ! nvv4l2decoder 
                ! nvvidconv compute-hw=1 ! videobox top=-1 bottom=-1 left=-1 right=-1 ! glupload ! glshader fragment={self.fragment_double_frame} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 
                ! queue2 ! tee name=t0 
                t0. ! queue2 ! nv3dsink sync=0 async=0 
                t0. ! queue2 ! nvv4l2h265enc 
                                    bitrate={self.cam.H265_REC_BITRATE} 
                                    peak-bitrate={self.cam.H265_REC_BITRATE} 
                                    control-rate=1 
                                    maxperf-enable=1 
                ! h265parse ! qtmux name=mux ! filesink sync=0 location={sink_file_uri}
            """
        elif(str(media_info['internet_media_type']).upper() == 'VIDEO/H264'):
            self.DEFAULT_PIPELINE = f"""
                filesrc location={source_file_uri} ! 
                qtdemux ! queue ! h264parse ! nvv4l2decoder 
                ! nvvidconv compute-hw=1 ! videobox top=-1 bottom=-1 left=-1 right=-1 ! glupload ! glshader fragment={self.fragment_double_frame} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 
                ! queue2 ! tee name=t0 
                t0. ! queue2 ! nv3dsink sync=0 async=0 
                t0. ! queue2 ! nvv4l2h264enc 
                                    bitrate={self.cam.H264_REC_BITRATE} 
                                    peak-bitrate={self.cam.H264_REC_BITRATE} 
                                    control-rate=1 
                                    maxperf-enable=1 
                ! h264parse ! qtmux name=mux ! filesink sync=0 location={sink_file_uri}
            """
        self.stop_preview()

        self.playPipeline()


    def video_player(self, set_hw:bool=False, source_file:str=None):


        self.camSelected = "play_video"

        source_file_uri     = "{0}{1}".format(str(self.cam.DROP_LOCATION.strip()), source_file.strip())
        print(source_file_uri)
        media_info = self.get_media_info(source_file_uri)


        self.DEFAULT_PIPELINE = None
        print(str(media_info['internet_media_type']).upper())

        if(str(media_info['internet_media_type']).strip().upper() == "VIDEO/H265"):
            self.DEFAULT_PIPELINE = f"""
                filesrc location={source_file_uri} ! qtdemux ! queue ! h265parse ! nvv4l2decoder ! queue2 ! nvegltransform ! nveglglessink 
            """
        elif(str(media_info['internet_media_type']).strip().upper() == "VIDEO/H264"):
            self.DEFAULT_PIPELINE = f"""
                filesrc location={source_file_uri} ! qtdemux ! queue ! h264parse ! nvv4l2decoder ! queue2 ! nvegltransform ! nveglglessink
            """
        
        # print(self.DEFAULT_PIPELINE)
        self.stop_preview()

        self.playPipeline()

    def pause_pipeline(self):

        self.pipeline.set_state(Gst.State.PAUSED)

    def ready_pipeline(self):

        self.pipeline.set_state(Gst.State.PLAYING)




    def playPipeline(self):
        self.pipeline   = Gst.parse_launch(self.DEFAULT_PIPELINE)
        self.bus        = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.pipeline.set_state(Gst.State.PLAYING)
        self.loop       = GLib.MainLoop()
        self.bus.connect("message", self.on_message, self.loop)
        self.loop.run()
        
    def on_message(self, bus: Gst.Bus, message: Gst.Message, loop: GLib.MainLoop):

        mtype = message.type

        if mtype == Gst.MessageType.EOS:

            print("PIPELINE EOS RECEIVED ************************************************")
            self.pipeline.set_state(Gst.State.NULL)
            loop.quit()
            self.pipeline = None
            # delete pipeline variable from memory
            del self.pipeline
                
            # time.sleep(2)
            # subprocess.call(["echo {0} | sudo -S nvpmodel -m {1}".format((str)(self.sys.password).strip(), self.sys.POWER_MODE)], shell=True)


        elif mtype == Gst.MessageType.ERROR:
            print("PIPELINE ERROR RECEIVED **********************************************")
            err, debug = message.parse_error()
            print(err, debug)
            loop.quit()

        elif mtype == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            print(err, debug)

        elif message.type == Gst.MessageType.STREAM_START:
            print("STREAM STARTED********************************************************")

            subprocess.call(["echo {0} | sudo -S nvpmodel -m {1}".format((str)(self.sys.password).strip(), self.sys.POWER_MODE)], shell=True)
            subprocess.call(["echo {0} | sudo -S jetson_clocks".format((str)(self.sys.password).strip())], shell=True)

            # self.streamStartedAction()
            print("working")


            mix_element = self.pipeline.get_by_name("mix")
            
            # Get the caps property from the mix element
            caps_property = mix_element.get_property("caps")
            print("work2")
            caps_string = caps_property.to_string()
            print("work3")
            print(caps_string)
            # self.changeCaps()

            if self.current_process=="calib":
                self.startAppsinkProcess()
                self.startPreview()
                pass

            if self.current_process=='x_calib':
                self.startAppsinkProcess_x()
                self.startPreview_x()
                pass

            if self.current_process=='stich_preview':
                # self.startAppsinkProcess()
                pass
          
    
    def stop_preview(self):
        # self.stop_recording()
        if hasattr(self, 'pipeline'):
            if self.pipeline is not None:
                # self.pipeline.send_event(Gst.Event.new_eos())
                # self.pipeline.set_state(Gst.State.PAUSED)


                #////////////////////////////////////
                if self.current_process =='calib':
                    self.appsrc.disconnect_by_func(self.on_need_data)
                    self.view_pipeline.set_state(Gst.State.PAUSED)
                    self.view_pipeline.set_state(Gst.State.NULL)

                    self.view_pipeline = None
                    del self.view_pipeline

                    time.sleep(3)
                #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

                # if self.current_process =='x_calib':
                #     self.appsrc.disconnect_by_func(self.on_need_data_x)
                #     self.view_pipeline.set_state(Gst.State.NULL)

                self.pipeline.set_state(Gst.State.NULL)
                self.loop.quit()
                print("stop eos send")

            self.pipeline = None
            self.bus = None
            self.loop = None

            del self.pipeline
        


    def stop_recording(self):
        if hasattr(self, 'pipeline'):
            if self.pipeline is not None:
                self.pipeline.send_event(Gst.Event.new_eos())
                print("PIPELINE EOS ISSUED **************************************************")




    def ChangePipelineParameters(self, property, mode,):
        
        Mode = mode

        if self.camSelected == "Left":
            src1 = self.pipeline.get_by_name('source1')
            src1.set_property(property, Mode)

        if self.camSelected == "Right":
            src2 = self.pipeline.get_by_name('source2')
            src2.set_property(property, Mode)
            
        if self.camSelected == "Stich":
            src1 = self.pipeline.get_by_name('source1')
            src2 = self.pipeline.get_by_name('source2')

            src1.set_property(property, Mode)
            src2.set_property(property, Mode)


        if property == 'wbmode':
            self.WBMODE = Mode
        if property == 'aeantibanding':
            self.AEANTI_BANDING = Mode
        if property == 'ee-mode':
            self.EDGE_ENHANCE = Mode
        if property == 'aelock' :
            self.AE_LOCK = Mode
        if property == 'awblock':
            self.AWB_LOCK = Mode
        if property == 'exposurecompensation':
            self.EXPOSURE_COMPENSATION = Mode
        if property == 'saturation':
            self.SATURATION = Mode
        if property == 'tnr-mode':
            self.TNR_MODE = Mode

        # print(property)

        self.source()

# wbmode, aeantibanding, ee-mode, aelock, awblock, exposurecompensation, saturation

    def dettachMasterBin(self):
		
        # self.recbin 	= self.pipeline.get_by_name("MASTER_BIN")
        self.ghostpad 	= self.recbin.get_static_pad("sink")
        self.teepad 	= self.ghostpad.get_peer()
		
        def blocking_pad_probe(pad, info):
            self.recbin.send_event(Gst.Event.new_eos())

            self.recbin.set_state(Gst.State.NULL)
            self.pipeline.remove(self.recbin)
            self.tee.release_request_pad(self.teepad)

            return Gst.PadProbeReturn.REMOVE
        self.teepad.add_probe(Gst.PadProbeType.BLOCK, blocking_pad_probe)
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "secondary pipeline dettached successfully", "\n")


'''
                                                    qp-range={self.cam.QP_RANGE_STREAM}
                                                    bitrate={self.cam.H264_STREAM_BITRATE}
                                                    insert-aud=1 
                                                    iframeinterval=30 
                                                    idrinterval=60

                                                    18,30:20,30:28,30
'''

'''
sensor-mode 0 => GST_ARGUS: 3840 x 2160 FR = 36.999999 fps Duration = 27027028 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
sensor-mode 1 => GST_ARGUS: 3840 x 2160 FR = 44.000001 fps Duration = 22727272 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
sensor-mode 2 => GST_ARGUS: 1944 x 1096 FR = 70.000001 fps Duration = 14285714 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
sensor-mode 3 => GST_ARGUS: 1296 x  732 FR =103.999996 fps Duration =  9615385 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
'''











        # if(hasattr(self, 'last_difference')):
        #     # if(abs(self.last_difference - difference) < 50):
        #     self.last_difference = difference
        #     self.caliculatePID(diff=self.last_difference)
        #     print("last_diff", self.last_difference)
        #     # else:
        #     #     pass
        # else:
        #     self.last_difference = difference
        #     self.caliculatePID(diff=self.last_difference)
        #     print("last_diff", self.last_difference)
