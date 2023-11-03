import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
from datetime import datetime
from controls.settings import Camera, CameraSettings, System, AudioSettings, StreamSettings
import sys
Gst.init(sys.argv)
import numpy as np
import cv2
import queue
import time
import subprocess
from pymediainfo import MediaInfo
from PyQt5.QtCore import *
from controls.motor import MotorParameters
import multiprocessing
import os

# from controls.remotecontrol import RemoteControler


class CameraStreamer:
    frame_update = None
    # fragment=None
    
    def __init__(self,apply_shader:bool=False):
        # Gst.init(sys.argv)
        self.cam 			= Camera()
        self.sys            = System()
        self.camSettings = CameraSettings()
        self.motors = MotorParameters()
        self.audio = AudioSettings()
        self.streamer = StreamSettings()

        self.apply_shader=apply_shader

        self.current_process = None

        self.RECORD_VIDEO_DROP_LOCATION = self.cam.DROP_LOCATION

        

        self.load_settings()
        self.width = 3840
        self.height = 2160
        self.fps = 30
        self.pipeline = None
        self.pipeline1 = None
        self.pipeline_state = None
        self.bus = None
        self.loop = None
        self.halfwidth = int(self.width/2)

        self.FHD_preview_width = 1920
        self.FHD_preview_height = 1080
        self.half_FHD_preview_width = int(self.FHD_preview_width/2)

        self.HD_preview_width = 1080
        self.HD_preview_height = 720
        self.half_HD_preview_width = int(self.HD_preview_width/2)


        quality = "4K"
        current_timestamp 	= datetime.now().strftime("%Y_%m_%d-%H%M%S")
        self.RECORDING_PATH = "{1}{2}_{0}.mp4".format(str(current_timestamp), str(self.cam.DROP_LOCATION.strip()), str(quality.strip()))

        self.camSelected = "Stich"

        self.SENSOR_MODE = 0 

        
        self.source()
        
        self.buildFragmentShaders()



        self.correction_checker = True

    




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
    

    def setCamSettings(self):

        self.applySettings = f"""
                        wbmode                  = {self.WBMODE} 
                        aeantibanding           = {self.AEANTI_BANDING} 
                        ee-mode                 = {self.EDGE_ENHANCE} 
                        awblock                 = {self.AWB_LOCK} 
                        exposurecompensation    = {self.EXPOSURE_COMPENSATION} 
                        saturation              = {self.SATURATION}
                        tnr-mode                = {self.TNR_MODE}
                        aelock                  = {self.AE_LOCK}
                        do-timestamp            = true
                            """


    def source(self):

        self.setCamSettings()

        self.source_1 = f'''
        nvarguscamerasrc sensor-id              = {self.cam.SOURCE_L}
                        name                    = source1 
                        
        '''

        self.source_2 = f'''
        nvarguscamerasrc sensor-id              = {self.cam.SOURCE_R}
                        name                    = source2

        '''

        if self.cam.ENABLE_CAMERA_SETTINGS==True:
            self.source_1 = self.source_1+self.applySettings
            self.source_2 = self.source_2+self.applySettings


    # PREVIEW 01
    def leftCameraPreview(self, set_hw:bool=False, width:int=3840, height:int=2160, fps:int=30):
        
        self.current_process = "preview"
        self.camSelected = "Left"

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)



        source = f"{self.source_1}! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)RGBA "
        if self.apply_shader:
            source = f"{self.source_1}! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! queue2 ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)RGBA "

        self.DEFAULT_PIPELINE   = f"{source} ! queue2 ! nvegltransform ! nveglglessink sync=0 async=0 window-height=2160 window-width=3840"
        
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()

        # nvvidconv ! queue2 ! nvegltransform ! nveglglessink sync=false async=false 
        # queue2 ! nv3dsink sync=0 async=0

    # PREVIEW 02
    def rightCameraPreview(self, set_hw:bool=False, width:int=3840, height:int=2160, fps:int=30):

        self.current_process = "preview"

        self.camSelected = "Right"

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        
        source = f"{self.source_2}! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)RGBA "
        if self.apply_shader:
            source = f"{self.source_2}! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! queue ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)RGBA "

        self.DEFAULT_PIPELINE   = f"{source} ! queue2 ! nvegltransform ! nveglglessink sync=0 async=0 window-height=2160 window-width=3840"
        
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()
        

    def sideBysidePreview(self, fps:int=30,):


        self.camSelected = "Stich"
        self.current_process = "streaming"


        width       = 3840
        height      = 2160

        sensor_mode = 0
            # fps         = 44

        # fisheye:  FOVH-185, FOVV-130
        # comp_width = 1920
        # comp_height = 2160

        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
        comp_width = int((width - (self.cam.CROP_WIDTH)*2) / 2)

        frame_width = comp_width*2
        print( "Frame width", frame_width)

        # comp_width = comp_width if self.cam.h265_full_width or quality != "2160p" else int(comp_width/2)

        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "

        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "
        

        self.DEFAULT_PIPELINE   = f"""
                    multiqueue name=mqueue sync-by-running-time=true use-buffering=true
                    nvcompositor name=comp 
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0
                                t0. ! nvvidconv ! nv3dsink sync=false async=false window-height=2160 window-width=3840
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.
                    {source_r} ! mqueue.sink_2 mqueue.src_2 ! comp.
                """
        
        print(self.DEFAULT_PIPELINE)
        self.playPipeline()

        pass


   
    def captureImage(self, set_hw:bool=False, fps:int=10, quality:str="1080p", mode:str="sbs"):


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

        comp_width = int((width - (self.cam.CROP_WIDTH)*2))
        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
        
        comp_width = comp_width if (self.cam.h265_full_width or quality != "2160p") else int(comp_width/2)


        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), format=(string)NV12, framerate=(fraction){fps}/1 , width=(int){width}, height=(int){width} ! tee name=t1 ! nvvidconv compute-hw=1 ! video/x-raw "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), format=(string)NV12, framerate=(fraction){fps}/1 ,width=(int){width}, height=(int){width} ! tee name=t1 ! nvvidconv compute-hw=1 ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! queue ! gldownload "

        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), format=(string)NV12, framerate=(fraction){fps}/1 ,width=(int){width}, height=(int){width} ! tee name=t2 !nvvidconv compute-hw=1 ! video/x-raw "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), format=(string)NV12, framerate=(fraction){fps}/1 ,width=(int){width}, height=(int){width} ! tee name=t2 ! nvvidconv compute-hw=1 ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! queue ! gldownload "


        self.DEFAULT_PIPELINE   = f'''
                    compositor name=comp background=black
                        sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::xpos={comp_width if mode=="sbs" else 0} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} sink_1::alpha={1 if mode=="sbs" else 0.5} ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 ! queue2 ! videorate ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! queue2 ! t2. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0 
                    {source_l} ! comp. 
                    {source_r} ! comp. 
              
                '''
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()



    def stream_4k(self, stream_key:str="key", set_hw:bool=False, quality:str="1080p", fps:int=30, stream_type:str="web"):

        self.camSelected = "Stich"

        self.DEFAULT_PIPELINE   = f"""
                 nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM), width=(int)3840, height=(int)2160, format=(string)NV12, framerate=(fraction)30/1 ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420 ! nvv4l2h264enc qp-range="24,24:28,28:30,30" control-rate=0 ! video/x-h264, stream-format=(string)byte-stream ! h264parse ! video/x-h264,stream-format=avc ! kvssink access-key="AKIATIYI4YO7VA356I7G" secret-key="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" aws-region="ap-northeast-1" stream-name="GIOVIEW"
                """
        
        self.playPipeline()



    # PREVIEW 04 
    # , set_hw:bool=False, fps:int=10, quality:str="2160p", mode:str="mono"
    def preview_3D(self, set_hw:bool=False, fps:int=10, quality:str="1080p", mode:str="sbs"):


        self.current_process = "preview"
        self.camSelected = "Stich"

                # if self.camSelected == "Stich":


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

        comp_width = int((width - (self.cam.CROP_WIDTH)*2))
        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
        
        comp_width = comp_width if (self.cam.h265_full_width or quality != "2160p") else int(comp_width/2)


        # Added due to slowness with shader--------------------(ishan)
        # if self.apply_shader :
        #     fps=2
        #-------------------------------------------------------



        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), format=(string)NV12, framerate=(fraction){fps}/1 , width=(int){width}, height=(int){width} ! tee name=t1 ! nvvidconv compute-hw=1 ! video/x-raw "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), format=(string)NV12, framerate=(fraction){fps}/1 ,width=(int){width}, height=(int){width} ! tee name=t1 ! nvvidconv compute-hw=1 ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! queue ! gldownload "

        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), format=(string)NV12, framerate=(fraction){fps}/1 ,width=(int){width}, height=(int){width} ! tee name=t2 !nvvidconv compute-hw=1 ! video/x-raw "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), format=(string)NV12, framerate=(fraction){fps}/1 ,width=(int){width}, height=(int){width} ! tee name=t2 ! nvvidconv compute-hw=1 ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! queue ! gldownload "


        

        self.DEFAULT_PIPELINE   = f'''
                    compositor name=comp background=black
                        sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::xpos={comp_width if mode=="sbs" else 0} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} sink_1::alpha={1 if mode=="sbs" else 0.5} ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 ! queue2 ! videorate ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! queue2 ! nvegltransform ! nveglglessink sync=0 async=0 window-x=0 window-y=0 window-width=3840 window-height=2160
                    {source_l} ! comp. 
                    {source_r} ! comp. 
              
                '''
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()



    def pipeline_appsink(self):
        self.current_process = "appsink"

        self.width  = 640
        self.height = 480
        self.fps    =  30

        # , width=(int){self.width}, height=(int){self.height}, framerate=(fraction){self.fps}/1

        self.DEFAULT_PIPELINE  = f"""
            multiqueue name=mqueue sync-by-running-time=true use-buffering=true
            nvcompositor name=comp 
                sink_0::xpos=0  
                sink_1::xpos={self.width} ! nvvidconv ! queue ! appsink name=appsink drop=1 emit-signals=1 caps="video/x-raw, format=(string)RGBA" max-buffers=1 throttle-time=100000000
            nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM), format=(string)NV12, width=(int){self.width}, height=(int){self.height}, framerate=(fraction){self.fps}/1 ! mqueue.sink_0 mqueue.src_0 ! comp.sink_0
            nvarguscamerasrc sensor-id=1 ! video/x-raw(memory:NVMM), format=(string)NV12, width=(int){self.width}, height=(int){self.height}, framerate=(fraction){self.fps}/1 ! mqueue.sink_1 mqueue.src_1 ! comp.sink_1
        """
        
        print(self.DEFAULT_PIPELINE)
        self.playPipeline()

    def videoPlayerNew(self):


        self.camSelected = "newPlayer"


        source_file_uri = "/media/giocam3d/GIOVIEW/Recordings/UHD_150556.mp4"



        self.DEFAULT_PIPELINE = f"""
            filesrc location={source_file_uri} ! qtdemux ! queue ! h264parse ! nvv4l2decoder ! nvvidconv ! queue ! appsink name=appsink drop=1 emit-signals=1 caps="video/x-raw, format=(string)RGBA" max-buffers=1 throttle-time=100000000
            """

        self.stop_preview()
        
        self.playPipeline()

    
    def startAppsinkProcess(self):
        
        self.appsink = self.pipeline.get_by_name("appsink")
        self.appsink.connect("new-sample", self.startPushBufferstoQueue)

        # self.appsrc=self.pipeline.get_by_name('source')
        # self.appsrc.connect('need-data', self.on_need_data)

        pass

    def startPushBufferstoQueue(self, appsink):

    
        sample = appsink.get_property("last-sample")

        if sample is not None:
            # get the buffer from the sample

            buffer = sample.get_buffer()
            data = buffer.extract_dup(0, buffer.get_size())
            
            caps = sample.get_caps()
            # sink_format = caps.get_structure(0).get_value('format')
            sink_height = caps.get_structure(0).get_value('height')
            sink_width  = caps.get_structure(0).get_value('width')
            # print("before size:", sink_height, sink_width)
            arry = np.ndarray(shape=(sink_height, sink_width, 4), buffer=data, dtype=np.uint8)

            # arry = cv2.cvtColor(arry, cv2.COLOR_BGRA2GRAY)
            self.frame_update = arry

            # cv2.imshow("new", arry)

            # self.labelViewer(frame=arry)




 # STREAM RTMP   # Edit by ishan
    def localStream2VR(self, vrIPAddress , fps:int=30, quality:str="1080p",):
        self.current_process = "streaming"

        self.camSelected = "Stich"


        sensor_mode=2

        width      = 1920
        height     = 1080

        localhost = vrIPAddress

        comp_width=int(width/2)
        comp_height=int(height)
        

        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 "
        
        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 "
        
      
        self.DEFAULT_PIPELINE   = f"""
                    nvcompositor name=comp
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! video/x-raw(memory:NVMM) ! nv3dsink sync=0 async=0 window-height=2160 window-width=3840
                            t0. ! queue2 ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420
                            ! queue2 ! nvvidconv ! nvjpegenc ! rndbuffersize ! queue2 ! udpsink host={localhost} port=3001 sync=0 async=0
                    {source_l} ! comp.
                    {source_r} ! comp.
                """
        
        print(self.DEFAULT_PIPELINE)
        self.playPipeline()
        




    # STREAM RTMP
    def stream_rtmp_4k__(self, fps:int=30, streamService:str="medialive"):

        self.camSelected = "Stich"
        self.current_process = "streaming"

        streamurl = f"{self.cam.STREAM_URL_4K_MEDIALIVE}"

        if streamService=='wowza':

            streamurl = f"{self.cam.STREAM_URL_4K_WOWZA}"

        if streamService=='medialive_h264':

            streamurl = f"{self.cam.STREAM_URL_4K_MEDIALIVE_H265}"


        width       = 3840
        height      = 2160

        sensor_mode = 0
            # fps         = 44

        # fisheye:  FOVH-185, FOVV-130

        # claculate cropping of the frames
        # left    = self.cam.CROP_WIDTH
        # right   = int(width - self.cam.CROP_WIDTH)
        # top     = self.cam.CROP_HEIGHT
        # bottom  = int(height - self.cam.CROP_HEIGHT)

        # comp_width = int((width - (self.cam.CROP_WIDTH)*2)/2)
        # comp_height= int((height - (self.cam.CROP_HEIGHT)*2))

        comp_width = 1920
        comp_height = 2160
        
        # comp_width = comp_width if self.cam.h265_full_width or quality != "2160p" else int(comp_width/2)

        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "

        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "
        

        self.DEFAULT_PIPELINE   = f"""
                    multiqueue name=mqueue sync-by-running-time=true use-buffering=true
                    nvcompositor name=comp 
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0
                                t0. ! nv3dsink sync=false async=false
                                t0. ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420 ! queue2 ! nvv4l2h264enc
                                                    peak-bitrate={self.cam.H264_STREAM_4K_BITRATE}
                                                    control-rate=0
                                                    insert-aud=1 
                                                    iframeinterval=30 
                                                    qp-range={self.cam.QP_RANGE_RECORD}
                                                    idrinterval=60 ! h264parse ! flvmux name=mux streamable=1 ! queue2 ! rtmpsink sync=false async=false location={streamurl} alsasrc do-timestamp=1 ! audio/x-raw ! queue2 ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! aacparse ! queue2 ! mux.
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.
                    {source_r} ! mqueue.sink_2 mqueue.src_2 ! comp.
                """
        
        print(self.DEFAULT_PIPELINE)
        self.playPipeline()

    # STREAM RTMP



    # STREAM RTMP
    def stream_rtmp_4k(self, streamService:str="medialive", bitrate:int=20000):

        fps = self.streamer.FPS_4K
        print(fps)
        self.camSelected = "Stich"
        self.current_process = "streaming"

        streamurl = f"{self.cam.STREAM_URL_4K_MEDIALIVE}"

        if streamService=='wowza':

            streamurl = f"{self.cam.STREAM_URL_4K_WOWZA}"

        if streamService=='medialive_h264':

            streamurl = f"{self.cam.STREAM_URL_4K_MEDIALIVE_H265}"

        width       = 3840
        height      = 2160

        sensor_mode = 0

        bitrate = int(bitrate*1000)

            # fps         = 44

        # fisheye:  FOVH-185, FOVV-130
        # comp_width = 1920
        # comp_height = 2160

        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
        comp_width = int((width - (self.cam.CROP_WIDTH)*2) / 2)

        frame_width = comp_width*2
        print( "Frame width", frame_width)

        # comp_width = comp_width if self.cam.h265_full_width or quality != "2160p" else int(comp_width/2)

        source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "

        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
        if self.apply_shader:
            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "
        

        self.DEFAULT_PIPELINE   = f"""
                    multiqueue name=mqueue sync-by-running-time=true use-buffering=true
                    nvcompositor name=comp 
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0
                                t0. ! nv3dsink sync=false async=false window-height=2160 window-width=3840
                                t0. ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420 ! queue2 ! nvv4l2h264enc
                                                    bitrate={bitrate}
                                                    control-rate=1
                                                    insert-aud=1 
                                                    iframeinterval=30 
                                                    idrinterval=60 ! h264parse ! flvmux name=mux streamable=1 ! queue2 ! rtmpsink sync=false async=false location={streamurl} alsasrc do-timestamp=1 ! audio/x-raw ! queue2 ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! aacparse ! queue2 ! mux.
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.
                    {source_r} ! mqueue.sink_2 mqueue.src_2 ! comp.
                """
        
        print(self.DEFAULT_PIPELINE)
        self.playPipeline()
        # peak-bitrate={bitrate}

    # STREAM RTMP




#Stream
    # Full Hd stream
    def stream_rtmp(self, stream_key:str="key", set_hw:bool=False, quality:str="1080p", stream_type:str="web"):

        fps = self.streamer.FPS_FHD

        self.camSelected = "Stich"
        self.current_process = "streaming"

        # url = 'rtmp://192.168.1.95/live/'
        # key = 'livestream'

        url = 'rtmp://54.172.159.142:1935/test1/'
        key = 'live1'

        # stream_key = 'sk_ap-northeast-1_ZpHxXdQE4ePi_Tt8kBVqcCeaj1QoGRtGfnq8ldntRPc'

        if stream_type=="web":
            streamurl = f"{str(self.cam.CLOUD_URL_RTMP).strip()}{str(stream_key).strip()}"

        
        if stream_type=="local":
             streamurl = f"{url}{key}"


        width      = 1920  
        height     = 1080   

        sensor_mode = 1

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
                    multiqueue name=mqueue sync-by-running-time=true use-buffering=true
                    nvcompositor name=comp
                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                        sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! queue2 ! tee name=t0 
                                t0. ! queue2 ! nvvidconv ! video/x-raw(memory:NVMM) ! nv3dsink window-width=1920 window-height=1080 sync=false async=false
                                t0. ! queue2 ! video/x-raw(memory:NVMM) !
                                    nvvidconv ! video/x-raw(memory:NVMM), format=(string)I420 ! queue2 ! nvv4l2h264enc
                                                    bitrate={self.cam.H264_STREAM_BITRATE}
                                                    insert-aud=1 
                                                    iframeinterval=30 
                                                    idrinterval=60 
                                                    control-rate=1
                                                        ! h264parse ! flvmux name=mux streamable=true ! queue2 ! rtmpsink async=1 sync=1 location={streamurl} alsasrc do-timestamp=1 ! audio/x-raw, format=S24_32LE, rate=48000 ! queue2 ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! aacparse ! queue2 ! mux.
                    {source_l} ! mqueue.sink_1 mqueue.src_1 ! comp.
                    {source_r} ! mqueue.sink_2 mqueue.src_2 ! comp.
            
                """
        
        # alsasrc do-timestamp=1 ! audio/x-raw, format=S24_32LE, rate=48000 ! queue2 ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! aacparse ! queue2 ! mux.
        # nvegltransform ! nveglglessink sync=0 async=0 
                # rtmpsink location={streamurl} async=0 sync=1
            # filesink sync=0 qos=1 location={rec_file_uri}
        # queue2 ! video/x-h264, stream-format=(string)byte-stream ! h264parse
        # nvvidconv ! queue2 ! nvegltransform ! nveglglessink sync=0 async=0 window-x=0 window-y=0 window-width=3840 window-height=2160
        print(self.DEFAULT_PIPELINE)

        self.playPipeline()



    # RECORD H264

    def record_h264(self, set_hw:bool=False, quality:str="2160p", file_type:str="mp4"):

        self.camSelected = "Stich"

        self.current_process = "recording_h264"

        fps = self.cam.FPS

        if (quality=="720p"):
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  += 8
            self.cam.CROP_HEIGHT += 6

            sensor_mode= 3

            comp_width = int((width - (self.cam.CROP_WIDTH)*2))

            # fps        = 100

        elif(quality=="1080p"):

            width      = 1944   #1920 + 24
            height     = 1096   #1080 + 16
            
            self.cam.CROP_WIDTH  += 12
            self.cam.CROP_HEIGHT += 8

            sensor_mode= 2

            comp_width = int((width - (self.cam.CROP_WIDTH)*2))

            # fps        = 70

        else:
            width      = 3840
            height     = 2160

            sensor_mode= 1

            comp_width = int((width - (self.cam.CROP_WIDTH)*2)/2)

            # fps        = 44

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
        
        rec_file_uri     = "{2}{4}{3}_{0}.{1}".format(str(datetime.now().strftime("%H%M%S")), file_type, str(self.cam.DROP_LOCATION.strip()),("HD" if quality.strip() == "720p" else ("FHD" if quality.strip() == "1080p" else "UHD")), "SH_" if self.apply_shader else "")

        # select the muxing pattern
        mux = None

        if file_type == "mp4":
            mux = "qtmux"
        elif file_type == "mkv":
            mux = "matroskamux"
        elif file_type == "avi":
            mux = "avimux"
        else :
            print("WARNING!: ", "System supports [mp4 | mkv] extensions only")

        self.DEFAULT_PIPELINE = f"""
                    multiqueue name=mqueue sync-by-running-time=true use-buffering=true
                    nvcompositor name=comp start-time-selection=1
                                    sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                                    sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! tee name=t0 
                    t0. ! queue2 ! nv3dsink sync=0 async=0 window-height=2160 window-width=3840
                    t0. ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 ! nvv4l2h264enc 
                            qos=true 
                            bitrate={self.cam.H264_REC_BITRATE}  
                            peak-bitrate=80000000 
                            control-rate=0 
                            maxperf-enable=true 
                            profile=Main ! video/x-h264, stream-format=(string)byte-stream, alignment=(string)au ! h264parse ! {mux} name=mux ! queue2 ! filesink sync=0 location={rec_file_uri} alsasrc do-timestamp=1 ! audio/x-raw, format=S24_32LE, rate=48000 ! queue2 ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! aacparse ! queue2 ! mux.
                    {source_l} ! mqueue.sink_0 mqueue.src_0 ! comp.sink_0 
                    {source_r} ! mqueue.sink_1 mqueue.src_1 ! comp.sink_1 
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
    def record_h265(self, set_hw:bool=False, quality:str="2160p", file_type:str="mp4"):
        
        try:

            fps = self.cam.FPS if self.cam.FPS <=30 else 30
            
            self.camSelected = "Stich"

            self.current_process = "recording_h265"

            # audio_device = self.audio.AUDIO_INPUT_DEVICE
            # audio_device = "USB Audio [USB Audio]"
            audio_device = "USB Audio [USB Audio]"
            # audio_device = "none"

            if audio_device == "none":
                device_name= ""
            else:
                device_name= f'audio_device={audio_device}'


            if (quality=="720p"):
                width      = 1296   #1280 + 16
                height     =  732   #720  + 12

                self.cam.CROP_WIDTH  += 8
                self.cam.CROP_HEIGHT += 6

                sensor_mode = 3
                # fps         = 100

            elif(quality=="1080p"):
                width       = 1944   #1920 + 24
                height      = 1096   #1080 + 16

                self.cam.CROP_WIDTH  += 12
                self.cam.CROP_HEIGHT += 8

                sensor_mode = 2
                # fps         = 70

            else:
                width       = 3840
                height      = 2160

                sensor_mode = 1
                # fps         = 44

            # fisheye:  FOVH-185, FOVV-130

            # claculate cropping of the frames
            left    = self.cam.CROP_WIDTH
            right   = int(width - self.cam.CROP_WIDTH)
            top     = self.cam.CROP_HEIGHT
            bottom  = int(height - self.cam.CROP_HEIGHT)

            comp_width = int((width - (self.cam.CROP_WIDTH)*2))
            comp_height= int((height - (self.cam.CROP_HEIGHT)*2))
            
            # comp_width = comp_width if self.cam.h265_full_width or quality != "2160p" else int(comp_width/2)
            comp_width = comp_width if self.cam.h265_full_width else int(comp_width/2)

            source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
            if self.apply_shader:
                source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "

            source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw(memory:NVMM), format=(string)I420 "
            if self.apply_shader:
                source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 "
            
            
            rec_file_uri     = "{2}{4}{3}_{0}.{1}".format(str(datetime.now().strftime("%H%M%S")), file_type, str(self.RECORD_VIDEO_DROP_LOCATION.strip()),("HD" if quality.strip() == "720p" else ("FHD" if quality.strip() == "1080p" else "UHD")), "SH_" if self.apply_shader else "")

            # select the muxing pattern
            mux = None

            if file_type == "mp4":
                mux = "qtmux"
            elif file_type == "mkv":
                mux = "matroskamux"
            elif file_type == "avi":
                mux = "avimux"
            else :
                print("WARNING!: ", "System supports [mp4 | mkv] extensions only")

            self.DEFAULT_PIPELINE = f""" 
                        multiqueue name=mqueue sync-by-running-time=true use-buffering=true 
                        nvcompositor name=comp 
                                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                                        sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! tee name=t0 
                        t0. ! queue2 ! nv3dsink sync=0 async=0 window-height=2160 window-width=3840
                        t0. ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 ! nvv4l2h265enc 
                                qos=true 
                                bitrate={self.cam.H265_REC_BITRATE}  
                                peak-bitrate=80000000 
                                control-rate=0 
                                maxperf-enable=true 
                                profile=Main ! video/x-h265, stream-format=(string)byte-stream, alignment=(string)au ! h265parse ! {mux} name=mux ! queue2 ! filesink sync=0 qos=1 location={rec_file_uri} alsasrc do-timestamp=1 {device_name} ! audio/x-raw, format=S24_32LE, rate=48000 ! queue2 ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! aacparse ! queue2 ! mux.
                        {source_l} ! mqueue.sink_0 mqueue.src_0 ! comp.sink_0 
                        {source_r} ! mqueue.sink_1 mqueue.src_1 ! comp.sink_1 
                    """
                                                                                                                                                                                                        #   device="hw:2,0"     device-name: "USB Audio [USB Audio]"       card-name: "Device [USB Audio Device]"
            if self.sys.SINGLE_CAM_OPERATION:
                self.DEFAULT_PIPELINE   = f"""
                        multiqueue name=mqueue sync-by-running-time=true use-buffering=true 
                        nvcompositor name=comp 
                                        sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} ! tee name=t0 
                        t0. ! queue2 ! nv3dsink sync=0 
                        t0. ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 ! nvv4l2h265enc 
                                qos=true 
                                bitrate={self.cam.H265_REC_BITRATE}  
                                peak-bitrate=80000000 
                                control-rate=0 
                                maxperf-enable=true 
                                profile=Main ! video/x-h265, stream-format=(string)byte-stream, alignment=(string)au ! h265parse ! {mux} name=mux ! queue2 ! filesink sync=0 qos=1 location={rec_file_uri} alsasrc do-timestamp=1 ! audio/x-raw, format=S24_32LE, rate=48000 ! queue2 ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! aacparse ! queue2 ! mux.
                        {source_l} ! mqueue.sink_0 mqueue.src_0 ! comp.sink_0 
                    """

            print(self.DEFAULT_PIPELINE)
            self.playPipeline()
    
        except:
        
            print(" Unable to Starrt Pipeline")




    def get_media_info(self, source_file:str):
        media_info_dict = {}

        print(source_file, "ffffffff")
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

        # general_track = media_info.general_tracks[0]
        # if general_track:
        #     media = general_track.format
        #     print(media, "   kkkkkkkkkkkkkkkkkkkkkkkk")

        return media_info_dict
    

    # APPLY FRAGMENT SHADER
    def post_process(self, set_hw:bool=False, source_file:str=None):
        self.camSelected = "play_video"

        source_file_uri     = "{0}{1}".format(str(self.cam.DROP_LOCATION.strip()), source_file.strip())
        sink_file_uri       = "{0}SH_{1}".format(str(self.cam.DROP_LOCATION.strip()), source_file.strip())

        media_info = self.get_media_info(source_file_uri)

        _, file_extension = os.path.splitext(source_file_uri.strip())
        if file_extension.lower() == '.mp4':
            demux = "qtdemux"
            mux = "qtmux"
        elif file_extension.lower() == '.mkv':
            demux = "matroskademux"
            mux = "matroskamux"
        else:
            pass

        self.DEFAULT_PIPELINE = None


        if(str(media_info['internet_media_type']).upper() == 'VIDEO/H265'):
            self.DEFAULT_PIPELINE = f"""
                filesrc location={source_file_uri} ! 
                {demux} ! queue ! h265parse ! nvv4l2decoder 
                ! nvvidconv compute-hw=1 ! videobox top=-1 bottom=-1 left=-1 right=-1 ! glupload ! glshader fragment={self.fragment_double_frame} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 
                ! queue2 ! tee name=t0 
                t0. ! queue2 ! nv3dsink sync=0 async=0 window-height=2160 window-width=3840
                t0. ! queue2 ! nvv4l2h265enc 
                                    bitrate={self.cam.H265_REC_BITRATE} 
                                    peak-bitrate={self.cam.H265_REC_BITRATE} 
                                    control-rate=1 
                                    maxperf-enable=1 
                ! h265parse ! {mux} name=mux ! filesink sync=0 location={sink_file_uri}
            """
        elif(str(media_info['internet_media_type']).upper() == 'VIDEO/H264'):
            self.DEFAULT_PIPELINE = f"""
                filesrc location={source_file_uri} ! 
                {demux} ! queue ! h264parse ! nvv4l2decoder 
                ! nvvidconv compute-hw=1 ! videobox top=-1 bottom=-1 left=-1 right=-1 ! glupload ! glshader fragment={self.fragment_double_frame} ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)I420 
                ! queue2 ! tee name=t0 
                t0. ! queue2 ! nv3dsink sync=0 async=0 
                t0. ! queue2 ! nvv4l2h264enc 
                                    bitrate={self.cam.H264_REC_BITRATE} 
                                    peak-bitrate={self.cam.H264_REC_BITRATE} 
                                    control-rate=1 
                                    maxperf-enable=1 
                ! h264parse ! {mux} name=mux ! filesink sync=0 location={sink_file_uri}
            """
        self.stop_preview()

        self.playPipeline()

    def video_player(self, set_hw:bool=False, source_file:str=None):


        self.camSelected = "play_video"

        source_file_uri     = "{0}{1}".format(str(self.cam.DROP_LOCATION.strip()), source_file.strip())
        print(source_file_uri)
        media_info = self.get_media_info(source_file_uri)

        print(str(media_info), "ggg")


        _, file_extension = os.path.splitext(source_file_uri.strip())
        if file_extension.lower() == '.mp4':
            demuxer = "qtdemux"
        elif file_extension.lower() == '.mkv':
            demuxer = "matroskademux"
        else:
            pass
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        self.DEFAULT_PIPELINE = None
        print(str(media_info['internet_media_type']).upper())

        if(str(media_info['internet_media_type']).strip().upper() == "VIDEO/H265"):
            self.DEFAULT_PIPELINE = f"""
                filesrc location={source_file_uri} ! {demuxer} ! queue ! h265parse ! nvv4l2decoder ! nvvidconv ! queue2 ! nvegltransform ! nveglglessink sync=0 async=0 window-height=2160 window-width=3840
            """
        elif(str(media_info['internet_media_type']).strip().upper() == "VIDEO/H264"):
            self.DEFAULT_PIPELINE = f"""
                filesrc location={source_file_uri} ! {demuxer} ! queue ! h264parse ! nvv4l2decoder ! nvvidconv ! queue2 ! nvegltransform ! nveglglessink sync=0 async=0 window-height=2160 window-width=3840
            """
        
        # print(self.DEFAULT_PIPELINE)
        
        self.stop_preview()
        
        self.playPipeline()

    def pause_pipeline(self):

        self.pipeline.set_state(Gst.State.PAUSED)

    def ready_pipeline(self):

        self.pipeline.set_state(Gst.State.PLAYING)


    def playPipeline(self):

        try :

            self.pipeline   = Gst.parse_launch(self.DEFAULT_PIPELINE)
            self.bus        = self.pipeline.get_bus()
            self.bus.add_signal_watch()

            self.pipeline.set_state(Gst.State.PLAYING)
            self.loop       = GLib.MainLoop()
            
            self.bus.connect("message", self.on_message, self.loop)
            # self.bus.connect("message::qos", self.on_quality_of_service)

            self.loop.run()
    
        except:
            print("Unable to Play the pipeline")

    def on_message(self, bus: Gst.Bus, message: Gst.Message, loop: GLib.MainLoop):

        mtype = message.type
        # print("MESSAGE TYPE: ", mtype)

        if mtype == Gst.MessageType.EOS:
            print("PIPELINE EOS RECEIVED ************************************************")
            self.pipeline.set_state(Gst.State.PAUSED)
            time.sleep(2)
            self.pipeline.set_state(Gst.State.NULL)
            loop.quit()

            self.pipeline_state = None

            self.pipeline = None

            del self.pipeline


        elif mtype == Gst.MessageType.ERROR:

            err, debug = message.parse_error()
            print("", err, debug)

            self.pipeline.set_state(Gst.State.NULL)

            loop.quit()

            self.pipeline = None
            del self.pipeline

            # subprocess.call(["echo {0} | sudo -S systemctl restart nvargus-daemon".format(self.sys.password)], shell=True)
            

        elif mtype == Gst.MessageType.WARNING:
            print("PIPELINE WARNING RECEIVED ********************************************")
            err, debug = message.parse_warning()
            print(err, debug)

        elif mtype == Gst.MessageType.QOS:
            print("PIPELINE QOS MESSAGE *************************************************")
            sname = message.src.get_name()
            live, t_running, t_stream, t_timestamp, drop_dur = message.parse_latency()
            print("Qos Message: ", sname)


        elif message.type == Gst.MessageType.STREAM_START:
            print("STREAM STARTED********************************************************")

            # Commended these 3 lines  nov 03--------------
            
            #subprocess.call(["echo {0} | sudo -S nvpmodel -m {1}".format((str)(self.sys.password).strip(), self.sys.POWER_MODE)], shell=True)
            #subprocess.call(["echo {0} | sudo -S jetson_clocks".format((str)(self.sys.password).strip())], shell=True)
            #time.sleep(2)
            
            #-----------------------------------------------


                        # self.streamStartedAction()

            self.pipeline_state = True

            if self.current_process=='appsink':
                
                # self.startPushBufferstoQueue()
                self.startAppsinkProcess()
                pass

            if self.current_process== "newPlayer":
                
                pass



         
    def stop_preview(self):
        # self.stop_recording()
        if hasattr(self, 'pipeline'):
            if self.pipeline is not None:
                self.pipeline.send_event(Gst.Event.new_eos())
                # self.pipeline.set_state(Gst.State.PAUSED)

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




# rtmp://a5ad0a0ae96b.entrypoint.cloud.wowza.com/app-h52g05S8/378e5444 (15.207.84.163) 
# rtmp://9142d7558842.entrypoint.cloud.wowza.com/app-G2c04053/1ba5bb33

# CROP_WIDTH=425