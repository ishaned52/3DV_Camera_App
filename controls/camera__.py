import subprocess

from controls.settings import Camera
from time import sleep

class CameraParameters():

    conf = Camera()

    # v4l2-ctl --device=/dev/video0 --set-ctrl=vertical_flip=0

    # INIT CAMERA PARAMS
    def __init__(self):
        self.cam_defaults = {
            'brightness': 0,                # min=-15 max=15 step=1 default=0 value=0 flags=slider
            'contrast': 4,                  # min=0 max=30 step=1 default=4 value=4 flags=slider
            'saturation': 18,               # min=0 max=60 step=1 default=18 value=18 flags=slider
            'white_balance_automatic': 1,   # default=1 value=1
            'white_balance_temperature':5000, # min=10 max=10000 step=10 default=5000 value=5000
            'gamma': 220,                   # min=40 max=500 step=1 default=220 value=220 flags=slider
            'gain': 6,                      # min=1 max=50 step=1 default=6 value=6
            'horizontal_flip': 0,           # default=0 value=0
            'vertical_flip': 0,             # default=0 value=0
            'sharpness':16,                 # min=1 max=127 step=1 default=16 value=16 flags=slider
            'exposure_auto': 0,             # min=0 max=2 default=0 value=0
            'exposure_time_absolute': 333,  # min=1 max=10000 step=1 default=333 value=333
            'exposure_compensation': 32000, # min=8000 max=1000000 step=1 default=32000 value=32000 flags=slider
            'roi_exposure': 32896,          # min=0 max=65535 step=1 default=32896 value=32896 flags=slider
            'pan_absolute': 0,              # min=-648000 max=648000 step=1 default=0 value=0
            'tilt_absolute': 0,             # min=-648000 max=648000 step=1 default=0 value=0
            'zoom_absolute': 100,           # min=100 max=800 step=1 default=100 value=100
            'ihdr': 0,                      # min=0 max=5 default=0 value=0
            'frame_sync': 1,                # min=0 max=2 default=1 value=1
            'bypass_mode': 0,               # min=0 max=1 default=0 value=0
            'override_enable': 0,           # min=0 max=1 default=0 value=0
            'height_align': 1,              # min=1 max=16 step=1 default=1 value=1
            'size_align': 0                 # min=0 max=2 default=0 value=0
        }
    
    
    # LOAD CAMERA DEFAULT SETINGS
    def setDefaults(self, cam=None):
        for key in self.cam_defaults:
            self.writeValue(str(key), str(self.cam_defaults[key]), cam)
            sleep(0.01)
    
    # HORIZONTAL FLIP
    def frameHorizontalFlip(self, cam=None, val= False):
        self.writeValue(str("horizontal_flip"), str(int(val)), cam)
    

    # VERTICAL FLIP
    def frameVerticalFlip(self, cam=None, val= False):
        self.writeValue(str("vertical_flip"), str(int(val)), cam)
        
    # BRIGHTNESS
    def setBrightness(self, cam=None, val=0):
        if val >= -15 and val <= 15:
            self.writeValue(str("brightness"), str(int(val)), cam)
    
    # CONTRAST
    def setContrast(self, cam=None, val=4):
        if val >= 0 and val <= 30:
            self.writeValue(str("contrast"), str(int(val)), cam)
            
    # SATURATION
    def setSaturation(self, cam=None, val=18):
        if val >= 0 and val <= 60:
            self.writeValue(str("saturation"), str(int(val)), cam)
            
    # GAMMA
    def setGamma(self, cam=None, val=220):
        if val >= 40 and val <= 500:
            self.writeValue(str("gamma"), str(int(val)), cam)
            
    # GAIN
    def setGain(self, cam=None, val=6):
        if val >= 1 and val <= 50:
            self.writeValue(str("gain"), str(int(val)), cam)
        
    # SHARPNESS
    def setSharpness(self, cam=None, val=16):
        if val >= 1 and val <= 127:
            self.writeValue(str("sharpness"), str(int(val)), cam)
    
    # EXPOSURE TIME
    def setExposureTime(self, cam=None, val=333):
        if val >= 1 and val <= 10000:
            self.writeValue(str("exposure_time_absolute"), str(int(val)), cam)
    
    # EXPOSURE COMPENSATION
    def setExposureCompensation(self, cam=None, val=32000):
        if val >= 8000 and val <= 1000000:
            self.writeValue(str("exposure_compensation"), str(int(val)), cam)
            
    # ROI EXPOSURE
    def setROIExposure(self, cam=None, val=32896):
        if val >= 0 and val <= 65535:
            self.writeValue(str("roi_exposure"), str(int(val)), cam)
    
    # AUTO WHITE BALANCE
    def setAutoWhiteBalance(self, cam=None, val=1):
        if val >= 0 and val <= 1:
            self.writeValue(str("white_balance_automatic"), str(int(val)), cam)
    
    # WHITE BALANCE TEMPERATURE
    def setWhiteBalanceTemperature(self, cam=None, val=5000): #step 10
        if val >= 10 and val <= 10000:
            self.writeValue(str("white_balance_temperature"), str(int(val)), cam)
    
    
    
    # ZOOM ABSOLUTE
    def setZoomAbsolute(self, cam=None, val=100): #step 1
        if val >= 100 and val <= 800:
            self.writeValue(str("zoom_absolute"), str(int(val)), cam)
    
    # PAN ABSOLUTE
    def setPanAbsolute(self, cam=None, val=0): #step 1
        if val >= -648000 and val <= 648000:
            self.writeValue(str("pan_absolute"), str(int(val)), cam)
    
    # TILT ABSOLUTE
    def setTiltAbsolute(self, cam=None, val=0): #step 1
        if val >= -648000 and val <= 648000:
            self.writeValue(str("tilt_absolute"), str(int(val)), cam)
    
    # PROCESS V4L2 COMMAND
    def writeValue(self, paramKey:str, val:int, cam=None):
        if cam == "LEFT":
            subprocess.call(['v4l2-ctl -d /dev/video{} -c {}={}'.format(str(self.conf.SOURCE_L),   paramKey, str(int(val)))], shell=True)
        elif cam == "RIGHT":
            subprocess.call(['v4l2-ctl -d /dev/video{} -c {}={}'.format(str(self.conf.SOURCE_R),   paramKey, str(int(val)))], shell=True)
        else:
            subprocess.call(['v4l2-ctl -d /dev/video{} -c {}={}'.format(str(self.conf.SOURCE_L),   paramKey, str(int(val)))], shell=True)
            subprocess.call(['v4l2-ctl -d /dev/video{} -c {}={}'.format(str(self.conf.SOURCE_R),   paramKey, str(int(val)))], shell=True)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    '''
    v4l2-ctl -d /dev/video0 -c Width/Height=1280/720
    v4l2-ctl --all --device path/to/video_device
    for key in cam_props:
        subprocess.call(['v4l2-ctl -d /dev/video1 -c {}={}'.format(key, str(cam_props[key]))], shell=True)
    '''
    
    '''
    v4l2-ctl --all --device /dev/video0
    ecam_tk1_guvcview
    '''
    
    '''
    'brightness': 0,                # min=-15 max=15 st ep=1 default=0 value=0 flags=slider
            'contrast': 4,                  # min=0 max=30 step=1 default=4 value=4 flags=slider
            'saturation': 18,               # min=0 max=60 step=1 default=18 value=18 flags=slider
            'white_balance_automatic': 1,   # default=1 value=1
            'gamma': 220,                   # min=40 max=500 step=1 default=220 value=220 flags=slider
            'gain': 6,                      # min=1 max=50 step=1 default=6 value=6
            'horizontal_flip': 0,           # default=0 value=0
            'vertical_flip': 0,             # default=0 value=0
            'white_balance_temperature':5000, # min=10 max=10000 step=10 default=5000 value=5000
            'sharpness':16,                 # min=1 max=127 step=1 default=16 value=16 flags=slider
            'exposure_auto': 0,             # min=0 max=2 default=0 value=0
            'exposure_time_absolute': 333,  # min=1 max=10000 step=1 default=333 value=333
            'exposure_compensation': 32000, # min=8000 max=1000000 step=1 default=32000 value=32000 flags=slider
            'roi_exposure': 32896,          # min=0 max=65535 step=1 default=32896 value=32896 flags=slider
            'pan_absolute': 0,              # min=-648000 max=648000 step=1 default=0 value=0
            'tilt_absolute': 0,             # min=-648000 max=648000 step=1 default=0 value=0
            'zoom_absolute': 100,           # min=100 max=800 step=1 default=100 value=100
            'ihdr': 0,                      # min=0 max=5 default=0 value=0
            'frame_sync': 1,                # min=0 max=2 default=1 value=1
            'bypass_mode': 0,               # min=0 max=1 default=0 value=0
            'override_enable': 0,           # min=0 max=1 default=0 value=0
            'height_align': 1,              # min=1 max=16 step=1 default=1 value=1
            'size_align': 0                 # min=0 max=2 default=0 value=0
            'write_isp_format': 1,          # min=1 max=1 step=1 default=1 value=1
            'sensor_signal_properties': 0,  # min=0 max=4294967295 step=1 default=0 [30][18] flags=read-only, has-payload
            'sensor_image_properties': 0,   # min=0 max=4294967295 step=1 default=0 [30][16] flags=read-only, has-payload
            'sensor_control_properties': 0, # min=0 max=4294967295 step=1 default=0 [30][36] flags=read-only, has-payload
            'sensor_dv_timings': 0,         # min=0 max=4294967295 step=1 default=0 [30][16] flags=read-only, has-payload
            'low_latency_mode': 0,          # default=0 value=0
            'preferred_stride': 0,          # min=0 max=65535 step=1 default=0 value=0
            'sensor_modes': 0,              # min=0 max=30 step=1 default=30 value=6 flags=read-only
    '''
