import subprocess

from controls.settings import Camera
from time import sleep

class CameraParameters():

    conf = Camera()

    # v4l2-ctl --device=/dev/video0 --set-ctrl=vertical_flip=0

    # INIT CAMERA PARAMS
    def __init__(self):

        
        # self.load_current_values
        # output = subprocess.check_output(['lsb_release', '-a'])
        # output = subprocess.check_output(['v4l2-ctl' '-d' '/dev/video0' '-C' 'exposure'])
        # output = subprocess.check_output(['v4l2-ctl -d /dev/video0 -C exposure'])
        #  v4l2-ctl -d /dev/video0 -C exposure
        # subprocess.call(['v4l2-ctl -d /dev/video{} -c {}={}'.format(str(self.conf.SOURCE_R),   paramKey, str(int(val)))], shell=True)
        # print(output.decode())
        variable = 'exposure'
        command = f'v4l2-ctl -d /dev/video0 -C {variable}'
        output = subprocess.check_output(command, shell=True)
        output_str = output.decode('utf-8')
        variable=variable +':'
        new_text = output_str.replace(variable, "")
        new_text = new_text.strip()
        self.new_text = int(new_text)


        self.cam_defaults = {
 
            'group_hold' : 0,               #  0x009a2003 (bool)   : default=0 value=0 flags=execute-on-write
            'hdr_enable' : 0,              #  0x009a2004 (intmenu): min=0 max=1 default=0 value=0
            'fuse_id'    :  0,              #  0x009a2007 (str)    : min=0 max=6 step=2 value='' flags=read-only, has-payload
            'sensor_mode': 0,              #  0x009a2008 (int64)  : min=0 max=4 step=1 default=0 value=0 flags=slider
            'gain'       : 0,               #  0x009a2009 (int64)  : min=0 max=300 step=3 default=0 value=0 flags=slider
            'exposure'   : 27027,             #  0x009a200a (int64)  : min=450 max=200000 step=1 default=27027 value=450 flags=slider
            'frame_rate' : 37000000,              #  0x009a200b (int64)  : min=5000000 max=37000000 step=1 default=37000000 value=5000000 flags=slider
            'bypass_mode' :    0,            #  0x009a2064 (intmenu): min=0 max=1 default=0 value=0
            'override_enable' : 0,           #  0x009a2065 (intmenu): min=0 max=1 default=0 value=0
            'height_align'    : 1,          #  0x009a2066 (int)    : min=1 max=16 step=1 default=1 value=1
            'size_align'      : 0,         #  0x009a2067 (intmenu): min=0 max=2 default=0 value=0
            'write_isp_format': 1,          #  0x009a2068 (int)    : min=1 max=1 step=1 default=1 value=1
            'sensor_signal_properties' :0,  #  0x009a2069 (u32)    : min=0 max=4294967295 step=1 default=0 [30][18] flags=read-only, has-payload
            'sensor_image_properties'  :0, #  0x009a206a (u32)    : min=0 max=4294967295 step=1 default=0 [30][16] flags=read-only, has-payload
            'sensor_control_properties':0, #  0x009a206b (u32)    : min=0 max=4294967295 step=1 default=0 [30][36] flags=read-only, has-payload
            'sensor_dv_timings'        :0, #  0x009a206c (u32)    : min=0 max=4294967295 step=1 default=0 [30][16] flags=read-only, has-payload
            'low_latency_mode'         :0, #  0x009a206d (bool)   : default=0 value=0
            'preferred_stride'         :0, #  0x009a206e (int)    : min=0 max=65535 step=1 default=0 value=0
            'sensor_modes'             :30 #  0x009a2082 (int)    : min=0 max=30 step=1 default=30 value=4 flags=read-only
        
        }

    
    # LOAD CAMERA DEFAULT SETINGS
    def setDefaults(self, cam=None):
        for key in self.cam_defaults:
            self.writeValue(str(key), str(self.cam_defaults[key]), cam)
            sleep(0.01)
    
    def groupHold(self, cam=None, val=False):
        self.writeValue(str("group_hold"), str(int(val)), cam)

    def setHdrEnable(self, cam=None, val=False):
        self.writeValue(str("hdr_enable"), str(int(val)), cam)
    
    def setSensorMode(self, cam=None, val=0):
        if val >=0 and val <=4:
            self.writeValue(str("sensor_mode"), str(int(val)), cam)

    def setGain(self, cam=None, val=267):
        
        if val >=0 and val <=300:
            self.writeValue(str("gain"), str(int(val)), cam)
        print("helllo")
    def setExposure(self, cam=None, val=27027):
        if val >=450 and val <=200000:
            self.writeValue(str("exposure"), str(int(val)), cam)

    def setFrameRate(self, cam=None, val=37000000):
        if val >=5000000 and val <=37000000:
            self.writeValue(str("frame_rate"), str(int(val)), cam)

    # def setBypassMode(self, cam=None, val=0):
    #     if val >=0 and val <=1:
    #         self.writeValue(str("bypass_mode"), str(int(val)), cam)

    def setHeightAlign(self, cam=None, val=1):
        if val >=1 and val <=16:
            self.writeValue(str("height_align"), str(int(val)), cam)

    def setSizeAlign(self, cam=None, val=1):
        if val >=0 and val <=2:
            self.writeValue(str("size_align"), str(int(val)), cam)

    def setSensorSignalProperties(self, cam=None, val=0):
        if val >=0 and val <=4294967295:
            self.writeValue(str("sensor_signal_properties"), str(int(val)), cam)

    def setSensorImageProperties(self, cam=None, val=0):
        if val >=0 and val <=4294967295:
            self.writeValue(str("sensor_image_properties"), str(int(val)), cam)       

    def setSensorControlProperties(self, cam=None, val=0):
        if val >=0 and val <=4294967295:
            self.writeValue(str("sensor_control_properties"), str(int(val)), cam) 

    def setSensorDvTimings(self, cam=None, val=0):
        if val >=0 and val <=4294967295:
            self.writeValue(str("sensor_dv_timings"), str(int(val)), cam) 

    def setPreferredStride(self, cam=None, val=0):
        if val >=0 and val <=65535:
            self.writeValue(str("preferred_stride"), str(int(val)), cam) 

    def setSensorModes(self, cam=None, val=30):
        if val >=0 and val <=30:
            self.writeValue(str("sensor_modes"), str(int(val)), cam)



    # PROCESS V4L2 COMMAND
    def writeValue(self, paramKey:str, val:int, cam=None):
        if cam == "LEFT":
            subprocess.call(['v4l2-ctl -d /dev/video{} -c {}={}'.format(str(self.conf.SOURCE_L),   paramKey, str(int(val)))], shell=True)
        elif cam == "RIGHT":
            subprocess.call(['v4l2-ctl -d /dev/video{} -c {}={}'.format(str(self.conf.SOURCE_R),   paramKey, str(int(val)))], shell=True)
        elif cam == None:
            subprocess.call(['v4l2-ctl -d /dev/video{} -c {}={}'.format(str(self.conf.SOURCE_L),   paramKey, str(int(val)))], shell=True)
            subprocess.call(['v4l2-ctl -d /dev/video{} -c {}={}'.format(str(self.conf.SOURCE_R),   paramKey, str(int(val)))], shell=True)
    
    
    # v4l2-ctl -d /dev/video0 -c gain=500