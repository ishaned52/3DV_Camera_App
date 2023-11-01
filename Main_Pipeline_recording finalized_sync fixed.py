import time
import subprocess
from datetime import datetime
from controls.settings import Camera, CameraSettings, System

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import sys
Gst.init(sys.argv)

from pymediainfo import MediaInfo
from PyQt5.QtCore import *


class CameraStreamer:

    def __init__(self):
        self.sys            = System()
        self.cam 			= Camera()
        self.camSettings    = CameraSettings()


        self.pipeline       = None
        self.bus            = None
        self.loop           = None



        self.source_1 = f'''
        nvarguscamerasrc sensor-id              = {self.cam.SOURCE_L}
                        wbmode                  = {self.camSettings.WBMODE} 
                        aeantibanding           = {self.camSettings.AEANTI_BANDING} 
                        ee-mode                 = {self.camSettings.EDGE_ENHANCE} 
                        awblock                 = {self.camSettings.AWB_LOCK} 
                        aelock                  = {self.camSettings.AE_LOCK} 
                        exposurecompensation    = {self.camSettings.EXPOSURE_COMPENSATION} 
                        saturation              = {self.camSettings.SATURATION}
                        tnr-mode                = {self.camSettings.TNR_MODE}
                        name                    = source1 
                        do-timestamp            = 1
        '''

        self.source_2 = f'''
        nvarguscamerasrc sensor-id              = {self.cam.SOURCE_R}
                        wbmode                  = {self.camSettings.WBMODE} 
                        aeantibanding           = {self.camSettings.AEANTI_BANDING} 
                        ee-mode                 = {self.camSettings.EDGE_ENHANCE} 
                        awblock                 = {self.camSettings.AWB_LOCK} 
                        aelock                  = {self.camSettings.AE_LOCK} 
                        exposurecompensation    = {self.camSettings.EXPOSURE_COMPENSATION} 
                        saturation              = {self.camSettings.SATURATION}
                        tnr-mode                = {self.camSettings.TNR_MODE}
                        name                    = source2 
                        do-timestamp            = 1
        '''


        # FRAGMENT SHADER DEFINITIONS
        self.apply_shader   = False

        # shader for single frame
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
                \" """ % (450, self.cam.HFOV, self.cam.VFOV)
        
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
            \" """ % (450, self.cam.HFOV, self.cam.VFOV)




    # PREVIEW SINGLE CAMERAS
    def preview_2D(self, set_hw:bool=False, quality:str="2160p", cam:str="left"):

        fps = self.cam.FPS

        if (quality=="720p"):
            width      = 1296   #1280 + 16
            height     =  732   #720  + 12

            self.cam.CROP_WIDTH  += 8
            self.cam.CROP_HEIGHT += 6

            sensor_mode= 3
            # fps        = 100

        elif(quality=="1080p"):

            width      = 1944   #1920 + 24
            height     = 1096   #1080 + 16
            
            self.cam.CROP_WIDTH  += 12
            self.cam.CROP_HEIGHT += 8

            sensor_mode= 2
            # fps        = 70

        else:
            width      = 3840
            height     = 2160

            sensor_mode= 1
            # fps        = 44

        # claculate cropping of the frames
        left    = self.cam.CROP_WIDTH
        right   = int(width - self.cam.CROP_WIDTH)
        top     = self.cam.CROP_HEIGHT
        bottom  = int(height - self.cam.CROP_HEIGHT)

        src = self.source_1 if cam == "left" else self.source_2

        source = f"{src} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), format=(string)NV12, width=(int){width}, height=(int){height}, framerate=(fraction){fps}/1 "
        if self.apply_shader:
            source = f"{src} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), format=(string)NV12, width=(int){width}, height=(int){height}, framerate=(fraction){fps}/1 ! nvvidconv compute-hw=1 top={top} bottom={bottom} left={left} right={right} ! video/x-raw, format=(string)RGBA ! videobox left=-1 right=-1 top=-1 bottom=-1 ! glupload ! glshader fragment={self.fragment} ! queue ! gldownload ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)RGBA "

        self.DEFAULT_PIPELINE   = f"{source} ! queue2 ! nv3dsink"
        
        self.start_pipeline()

    # PREVIEWS SBS, TOP-BOTTOM AND BLENDED
    def preview_3D(self, set_hw:bool=False, quality:str="1080p", mode:str="sbs"):

        fps = self.cam.FPS

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
                        sink_1::xpos={comp_width if mode=="sbs" else 0} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} sink_1::alpha={1 if mode=="sbs" else 0.5} ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 ! queue2 ! videorate ! video/x-raw(memory:NVMM), framerate=(fraction){fps}/1 ! queue2 ! nv3dsink sync=0 async=0 window-x=0 window-y=0 window-width=3840 window-height=2160
                    {source_l} ! comp. 
                    {source_r} ! comp. 
                    t1. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image1.jpg" throttle-time=500000000 sync=1 async=0 
                    t2. ! queue2 ! nvvidconv compute-hw=1 ! nvjpegenc ! queue2 ! multifilesink location="images/image2.jpg" throttle-time=500000000 sync=1 async=0               
                '''

        self.start_pipeline()

    # RECORD H264
    def record_h264(self, set_hw:bool=False, quality:str="2160p", file_type:str="mp4"):

        fps = self.cam.FPS if self.cam.FPS <=30 else 30

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
        
        rec_file_uri     = "{2}{3}_{0}.{1}".format(str(datetime.now().strftime("%H%M%S")), file_type, str(self.cam.DROP_LOCATION.strip()),("HD" if quality.strip() == "720p" else ("FHD" if quality.strip() == "1080p" else "UHD")))

        # select the muxing pattern
        mux = None

        if file_type == "mp4":
            mux = "qtmux"
        elif file_type == "mkv":
            mux = "matroskamux"
        else :
            print("WARNING!: ", "System supports [mp4 | mkv] extensions only")

        self.DEFAULT_PIPELINE = f"""
                    multiqueue name=mqueue sync-by-running-time=true use-buffering=true
                    nvcompositor name=comp start-time-selection=1
                                    sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                                    sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! tee name=t0 
                    t0. ! queue2 ! nv3dsink sync=0 
                    t0. ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 ! nvv4l2h264enc 
                            qos=true 
                            bitrate={self.cam.H265_REC_BITRATE}  
                            peak-bitrate=80000000 
                            control-rate=0 
                            maxperf-enable=true 
                            profile=Main ! video/x-h264, stream-format=(string)byte-stream, alignment=(string)au ! h264parse ! {mux} name=mux ! queue2 ! filesink sync=0 location={rec_file_uri} alsasrc do-timestamp=1 ! audio/x-raw, format=S24_32LE, rate=48000 ! queue2 ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! aacparse ! queue2 ! mux.
                    {source_l} ! mqueue.sink_0 mqueue.src_0 ! comp.sink_0 
                    {source_r} ! mqueue.sink_1 mqueue.src_1 ! comp.sink_1 
                """
        
        if self.sys.SINGLE_CAM_OPERATION:
            self.DEFAULT_PIPELINE   = f"""
                    multiqueue name=mqueue sync-by-running-time=true use-buffering=true
                    nvcompositor name=comp start-time-selection=1 sink_0::xpos=0 sink_0::ypos=0 ! tee name=t0 
                    t0. ! queue2 ! nv3dsink sync=0 
                    t0. ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 ! nvv4l2h264enc 
                            qos=true 
                            bitrate={self.cam.H265_REC_BITRATE}  
                            peak-bitrate=80000000 
                            control-rate=0 
                            maxperf-enable=true 
                            profile=Main ! video/x-h264, stream-format=(string)byte-stream, alignment=(string)au ! h264parse ! {mux} name=mux ! queue2 ! filesink sync=0 location={rec_file_uri} alsasrc do-timestamp=1 ! audio/x-raw, format=S24_32LE, rate=48000 ! queue2 ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! aacparse ! queue2 ! mux.
                    {source_l} ! mqueue.sink_0 mqueue.src_0 ! comp.sink_0 
                """
            
        self.start_pipeline()

    # RECORD H265
    def record_h265(self, set_hw:bool=False, quality:str="2160p", file_type:str="mp4"):
        
        fps = self.cam.FPS if self.cam.FPS <=30 else 30
        
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
        
        comp_width = comp_width if self.cam.h265_full_width or quality != "2160p" else int(comp_width/2)

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

        self.DEFAULT_PIPELINE = f""" 
                    multiqueue name=mqueue sync-by-running-time=true use-buffering=true 
                    nvcompositor name=comp 
                                    sink_0::interpolation-method={self.cam.INTERPOLATION} sink_0::xpos=0 sink_0::ypos=0 sink_0::width={comp_width} sink_0::height={comp_height} 
                                    sink_1::interpolation-method={self.cam.INTERPOLATION} sink_1::xpos={comp_width} sink_1::ypos=0 sink_1::width={comp_width} sink_1::height={comp_height} ! tee name=t0 
                    t0. ! queue2 ! nv3dsink sync=0 
                    t0. ! queue2 ! nvvidconv compute-hw=1 ! video/x-raw(memory:NVMM), format=(string)NV12 ! nvv4l2h265enc 
                            qos=true 
                            bitrate={self.cam.H265_REC_BITRATE}  
                            peak-bitrate=80000000 
                            control-rate=0 
                            maxperf-enable=true 
                            profile=Main ! video/x-h265, stream-format=(string)byte-stream, alignment=(string)au ! h265parse ! {mux} name=mux ! queue2 ! filesink sync=0 qos=1 location={rec_file_uri} alsasrc do-timestamp=1 ! audio/x-raw, format=S24_32LE, rate=48000 ! queue2 ! audioconvert ! audioresample ! queue2 ! voaacenc bitrate=128000 ! aacparse ! queue2 ! mux.
                    {source_l} ! mqueue.sink_0 mqueue.src_0 ! comp.sink_0 
                    {source_r} ! mqueue.sink_1 mqueue.src_1 ! comp.sink_1 
                """

        if self.sys.SINGLE_CAM_OPERATION:
            self.DEFAULT_PIPELINE   = f"""
                    multiqueue name=mqueue sync-by-running-time=true use-buffering=true 
                    nvcompositor name=comp sink_0::xpos=0 sink_0::ypos=0 ! tee name=t0 
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

        self.start_pipeline()
   
    # APP SINK PIPELINE
    def pipeline_appsink(self, set_hw:bool=False, quality:str="720p"):

        fps = self.cam.FPS if self.cam.FPS <=30 else 30
        
        if (quality=="720p"):
            width      = 1280
            height     =  720

        elif(quality=="1080p"):
            width       = 1920
            height      = 1080

        else:
            width       = 3840
            height      = 2160

        self.DEFAULT_PIPELINE  = f"""
            multiqueue name=mqueue sync-by-running-time=true use-buffering=true
            nvcompositor name=comp 
                sink_0::xpos=0  
                sink_1::xpos={width} ! nvvidconv ! queue ! appsink name=appsink drop=1 emit-signals=1 caps="video/x-raw, format=(string)RGBA" max-buffers=1 throttle-time=100000000
            nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM), format=(string)NV12, width=(int){width}, height=(int){height}, framerate=(fraction){fps}/1 ! mqueue.sink_0 mqueue.src_0 !  comp.sink_0
            nvarguscamerasrc sensor-id=1 ! video/x-raw(memory:NVMM), format=(string)NV12, width=(int){width}, height=(int){height}, framerate=(fraction){fps}/1 ! mqueue.sink_1 mqueue.src_1 !  comp.sink_1
        """
        
        self.start_pipeline()




    # APPLY FRAGMENT SHADER
    def post_process(self, set_hw:bool=False, source_file:str=None):

        source_file_uri     = f"{self.cam.DROP_LOCATION.strip()}{source_file.strip()}"
        sink_file_uri       = f"{source_file.strip()}SH_{source_file.strip()}"

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

        self.start_pipeline()

    # MEDIA PLAYER PIPELINE
    def play_media(self, set_hw:bool=False, source_file:str=None):
        source_file_uri     = f"{self.cam.DROP_LOCATION.strip()}{source_file.strip()}"

        media_info = self.get_media_info(source_file_uri)

        self.DEFAULT_PIPELINE = None

        if(str(media_info['internet_media_type']).strip().upper() == "VIDEO/H265"):
            self.DEFAULT_PIPELINE = f"""
                filesrc location={source_file_uri} ! qtdemux ! queue ! h265parse ! nvv4l2decoder ! queue2 ! nvegltransform ! nveglglessink 
            """
        elif(str(media_info['internet_media_type']).strip().upper() == "VIDEO/H264"):
            self.DEFAULT_PIPELINE = f"""
                filesrc location={source_file_uri} ! qtdemux ! queue ! h264parse ! nvv4l2decoder ! queue2 ! nvegltransform ! nveglglessink
            """

        self.start_pipeline()




    # DEFINE GSTREAMER MESSAGE EVENT LISTENERS
    def on_message(self, bus: Gst.Bus, message: Gst.Message, loop: GLib.MainLoop):

        mtype = message.type
        # print("MESSAGE TYPE: ", mtype)

        if mtype == Gst.MessageType.EOS:
            print("PIPELINE EOS RECEIVED ************************************************")
            self.pipeline.set_state(Gst.State.NULL)
            loop.quit()
            self.pipeline = None

            # delete pipeline variable from memory
            del self.pipeline

        elif mtype == Gst.MessageType.ERROR:
            print("PIPELINE ERROR RECEIVED **********************************************")
            err, debug = message.parse_error()
            print(err, debug)
            loop.quit()
            self.pipeline = None
            
            # delete pipeline variable from memory
            del self.pipeline

        elif mtype == Gst.MessageType.WARNING:
            print("PIPELINE WARNING RECEIVED ********************************************")
            err, debug = message.parse_warning()
            print(err, debug)

        elif mtype == Gst.MessageType.QOS:
            print("PIPELINE QOS MESSAGE *************************************************")
            sname = message.src.get_name()
            live, t_running, t_stream, t_timestamp, drop_dur = message.parse_latency()
            print(sname)
            print(live, t_running, t_stream, t_timestamp, drop_dur)

        elif message.type == Gst.MessageType.STREAM_START:
            print("STREAM STARTED********************************************************")
            subprocess.call(["echo {0} | sudo -S nvpmodel -m {1}".format((str)(self.sys.password).strip(), self.sys.POWER_MODE)], shell=True)
            subprocess.call(["echo {0} | sudo -S jetson_clocks".format((str)(self.sys.password).strip())], shell=True)
            time.sleep(2)

    # PAUSE PIPELINE
    def pause_pipeline(self):
        self.pipeline.set_state(Gst.State.PAUSED)

    # RESUME PIPELINE
    def resume_pipeline(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    # INITIALIZE AND START PIPELINE
    def start_pipeline(self):
        self.pipeline   = Gst.parse_launch(self.DEFAULT_PIPELINE)
        
        self.bus        = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message, self.loop)

        self.pipeline.set_state(Gst.State.PLAYING)

        self.loop       = GLib.MainLoop()
        self.loop.run()
    
    # FORCE EOS TO SHUTDOWN PIPELINE 
    def stop_pipeline(self):
        if hasattr(self, 'pipeline'):
            if self.pipeline is not None:
                self.pipeline.send_event(Gst.Event.new_eos())
                print("PIPELINE EOS ISSUED **************************************************")




    # UPDATE PIPELINE ELEMENT PROPERTY ONLINE
    def update_pipeline(self, set_hw:bool=False, element_name:str=None, property:str=None, set_value:any=None):
        # SET PROPERTY ON THE GO
        element = self.pipeline.get_by_name(element_name)
        element.set_property(property, set_value)


        # SAVE PARAMETER IN CONFIG FILE
        if property == 'wbmode':
            self.camSettings.WBMODE                 = set_value
        if property == 'aeantibanding':
            self.camSettings.AEANTI_BANDING         = set_value
        if property == 'ee-mode':
            self.camSettings.EDGE_ENHANCE           = set_value
        if property == 'aelock' :
            self.camSettings.AE_LOCK                = set_value
        if property == 'awblock':
            self.camSettings.AWB_LOCK               = set_value
        if property == 'exposurecompensation':
            self.camSettings.EXPOSURE_COMPENSATION  = set_value
        if property == 'saturation':
            self.camSettings.SATURATION             = set_value
        if property == 'tnr-mode':
            self.camSettings.TNR_MODE               = set_value

        self.camSettings.save()




    # READ MEDIA INFO
    def get_media_info(self, source_file:str):
        media_info_dict = {}
        
        media_info = MediaInfo.parse(source_file.strip())

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
    