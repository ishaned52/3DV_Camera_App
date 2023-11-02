from os.path import dirname, abspath, exists
import yaml
import serial

# import ruamel.yaml as yaml

class Motor():
    # power, speed
    M1 = [0,0]
    M2 = [0,0]
    M3 = [0,0]
    M4 = [0,0]
    M5 = [0,0]
    M6 = [0,0]
    M7 = [0,0]

    SEC_MTR_INVERSE_SEPERATION = False
    SEC_MTR_INVERSE_CONVERGENCE = False
    SEC_MTR_INVERSE_TILT =  False

    
    motor_file = "config/motor.yaml"

    def __init__(self) -> None:
        self.motor_file = dirname(dirname(dirname(abspath(__file__)))) + "/config/motor.yaml" if exists(dirname(dirname(dirname(abspath(__file__)))) + "/config/motor.yaml") else dirname(dirname(abspath(__file__))) + "/config/motor.yaml"
        self.load()


    def load(self):
        with open( self.motor_file, "r+") as stream:
            try:
                self.config = yaml.safe_load(stream)
                
                if 'M1' in self.config:
                    self.M1[0] = self.config['M1']['SPEED'] if 'SPEED' in self.config['M1'] else 0
                    self.M1[1] = self.config['M1']['POWER'] if 'POWER' in self.config['M1'] else 0
                if 'M2' in self.config:
                    self.M2[0] = self.config['M2']['SPEED'] if 'SPEED' in self.config['M2'] else 0
                    self.M2[1] = self.config['M2']['POWER'] if 'POWER' in self.config['M2'] else 0
                if 'M3' in self.config:
                    self.M3[0] = self.config['M3']['SPEED'] if 'SPEED' in self.config['M3'] else 0
                    self.M3[1] = self.config['M3']['POWER'] if 'POWER' in self.config['M3'] else 0
                if 'M4' in self.config:
                    self.M4[0] = self.config['M4']['SPEED'] if 'SPEED' in self.config['M4'] else 0
                    self.M4[1] = self.config['M4']['POWER'] if 'POWER' in self.config['M4'] else 0
                if 'M5' in self.config:
                    self.M5[0] = self.config['M5']['SPEED'] if 'SPEED' in self.config['M5'] else 0
                    self.M5[1] = self.config['M5']['POWER'] if 'POWER' in self.config['M5'] else 0
                if 'M6' in self.config:
                    self.M6[0] = self.config['M6']['SPEED'] if 'SPEED' in self.config['M6'] else 0
                    self.M6[1] = self.config['M6']['POWER'] if 'POWER' in self.config['M6'] else 0
                if 'M7' in self.config:
                    self.M7[0] = self.config['M7']['SPEED'] if 'SPEED' in self.config['M7'] else 0
                    self.M7[1] = self.config['M7']['POWER'] if 'POWER' in self.config['M7'] else 0

                if 'DIR_INVERSE_SEPERATION' in self.config:
                    self.DIR_INVERSE_SEPERATION = self.config['DIR_INVERSE_SEPERATION']

                if 'DIR_INVERSE_CONVERGENCE' in self.config:
                    self.DIR_INVERSE_CONVERGENCE = self.config['DIR_INVERSE_CONVERGENCE']

                if 'DIR_INVERSE_TILT' in self.config:
                    self.DIR_INVERSE_TILT = self.config['DIR_INVERSE_TILT']

                stream.close()
            except yaml.YAMLError as exc:
                print(exc)

    def save(self):
        with open(self.motor_file, "r+") as stream:
            try:
                self.config['M1']['SPEED'] = int(self.M1[0])
                self.config['M1']['POWER'] = int(self.M1[1])
                
                self.config['M2']['SPEED'] = int(self.M2[0])
                self.config['M2']['POWER'] = int(self.M2[1])
                
                self.config['M3']['SPEED'] = int(self.M3[0])
                self.config['M3']['POWER'] = int(self.M3[1])
                
                self.config['M4']['SPEED'] = int(self.M4[0])
                self.config['M4']['POWER'] = int(self.M4[1])
                
                self.config['M5']['SPEED'] = int(self.M5[0])
                self.config['M5']['POWER'] = int(self.M5[1])
                
                self.config['M6']['SPEED'] = int(self.M6[0])
                self.config['M6']['POWER'] = int(self.M6[1])
                
                self.config['M7']['SPEED'] = int(self.M7[0])
                self.config['M7']['POWER'] = int(self.M7[1])

                stream.seek(0)    
                stream.truncate()
                
                yaml.safe_dump(self.config, stream=stream, default_flow_style=False, allow_unicode=True)
                stream.close()
                
            except yaml.YAMLError as exc:
                print(exc)

class Camera():
    SOURCE_L = 0
    SOURCE_R = 1

    FPS = 30
    
    FRAME_WIDTH = 640
    FRAME_HEIGHT= 480

    YOUTUBE_STREAM_KEY=None
    CLOUD_STREAM_KEY=None
    DROP_LOCATION=None
    YOUTUBE_URL=None
    CLOUD_URL=None

    VR_ADDRESS="0.0.0.0"
 
    camera_file = "config/camera.yaml"

    H264_STREAM_BITRATE = 8500000
    H265_REC_BITRATE = 16000000
    H264_REC_BITRATE = 25000000

    FOVH=185.0
    FOVV=135.0

    INTERPOLATION="Bilinear"
    
    CROP_WIDTH = 100
    CROP_HEIGHT = 0

    QP_RANGE_STREAM = "18,30:20,30:28,30"
    QP_RANGE_RECORD = "18,30:20,30:28,30"

    def __init__(self) -> None:
        self.camera_file = dirname(dirname(dirname(abspath(__file__)))) + "/config/camera.yaml" if exists(dirname(dirname(dirname(abspath(__file__)))) + "/config/camera.yaml") else dirname(dirname(abspath(__file__))) + "/config/camera.yaml"
        self.load()
        
    def load(self):
        with open(self.camera_file, "r+") as stream:
            try:
                self.config = yaml.safe_load(stream)
                if 'SOURCE_L' in self.config:
                    self.SOURCE_L = self.config['SOURCE_L']
                
                if 'SOURCE_R' in self.config:
                    self.SOURCE_R = self.config['SOURCE_R']
                    
                if 'FRAME_WIDTH' in self.config:
                    self.FRAME_WIDTH = self.config['FRAME_WIDTH']
                    
                if 'FRAME_HEIGHT' in self.config:
                    self.FRAME_HEIGHT = self.config['FRAME_HEIGHT']

                if 'DROP_LOCATION' in self.config:
                    self.DROP_LOCATION = self.config['DROP_LOCATION']
                    
                if 'YOUTUBE_STREAM_KEY' in self.config:
                    self.YOUTUBE_STREAM_KEY = self.config['YOUTUBE_STREAM_KEY']

                if 'CLOUD_STREAM_KEY' in self.config:
                    self.CLOUD_STREAM_KEY = self.config['CLOUD_STREAM_KEY']
                
                if 'VR_ADDRESS' in self.config:
                    self.VR_ADDRESS = str(self.config['VR_ADDRESS'])

                if 'LEFT_IMAGE_LOCATION' in self.config:
                    self.LEFT_IMAGE_LOCATION = self.config['LEFT_IMAGE_LOCATION']

                if 'RIGHT_IMAGE_LOCATION' in self.config:
                    self.RIGHT_IMAGE_LOCATION = self.config['RIGHT_IMAGE_LOCATION']

                if 'YOUTUBE_URL' in self.config:
                    self.YOUTUBE_URL = self.config['YOUTUBE_URL']

                if 'CLOUD_URL_RTMP' in self.config:
                    self.CLOUD_URL_RTMP = self.config['CLOUD_URL_RTMP']

                if 'CLOUD_URL_RTMPS' in self.config:
                    self.CLOUD_URL_RTMPS = self.config['CLOUD_URL_RTMPS']

                if 'H264_STREAM_BITRATE' in self.config:
                    self.H264_STREAM_BITRATE = self.config['H264_STREAM_BITRATE']

                if 'H265_REC_BITRATE' in self.config:
                    self.H265_REC_BITRATE = self.config['H265_REC_BITRATE']

                if 'H264_REC_BITRATE' in self.config:
                    self.H264_REC_BITRATE = self.config['H264_REC_BITRATE']

                if 'HFOV' in self.config:
                    self.HFOV = self.config['HFOV']

                if 'VFOV' in self.config:
                    self.VFOV = self.config['VFOV']

                if 'INTERPOLATION' in self.config:
                    self.INTERPOLATION = self.config['INTERPOLATION']

                if 'h265_full_width' in self.config:
                    self.h265_full_width = self.config['h265_full_width']

                if 'QP_RANGE_STREAM' in self.config:
                    self.QP_RANGE_STREAM = self.config['QP_RANGE_STREAM']
                    
                if 'QP_RANGE_RECORD' in self.config:
                    self.QP_RANGE_RECORD = self.config['QP_RANGE_RECORD']

                if 'CROP_WIDTH' in self.config:
                    self.CROP_WIDTH = self.config['CROP_WIDTH']

                if 'CROP_HEIGHT' in self.config:
                    self.CROP_HEIGHT = self.config['CROP_HEIGHT']

                if 'H264_STREAM_4K_BITRATE' in self.config:
                    self.H264_STREAM_4K_BITRATE = self.config['H264_STREAM_4K_BITRATE']

                if 'STREAM_URL_4K_MEDIALIVE' in self.config:
                    self.STREAM_URL_4K_MEDIALIVE = self.config['STREAM_URL_4K_MEDIALIVE']

                if 'STREAM_URL_4K_WOWZA' in self.config:
                    self.STREAM_URL_4K_WOWZA = self.config['STREAM_URL_4K_WOWZA']

                if 'FPS' in self.config:
                    self.FPS = self.config['FPS']

                if 'ENABLE_4K_STREAM' in self.config:
                    self.ENABLE_4K_STREAM = self.config['ENABLE_4K_STREAM']

                if 'ENABLE_CAMERA_SETTINGS' in self.config:
                    self.ENABLE_CAMERA_SETTINGS = self.config['ENABLE_CAMERA_SETTINGS']

                if 'STREAM_URL_4K_MEDIALIVE_H265' in self.config:
                    self.STREAM_URL_4K_MEDIALIVE_H265 = self.config['STREAM_URL_4K_MEDIALIVE_H265']
                    


                stream.close()
            except yaml.YAMLError as exc:
                print(exc)

    def save(self):
        with open(self.camera_file, "r+") as stream:
            try:
                self.config['SOURCE_L']             = self.SOURCE_L
                self.config['SOURCE_R']             = self.SOURCE_R
                self.config['FRAME_WIDTH']          = self.FRAME_WIDTH
                self.config['FRAME_HEIGHT']         = self.FRAME_HEIGHT
                self.config['DROP_LOCATION']        = self.DROP_LOCATION
                self.config['YOUTUBE_STREAM_KEY']   = self.YOUTUBE_STREAM_KEY
                self.config['CLOUD_STREAM_KEY']     = self.CLOUD_STREAM_KEY
                self.config['VR_ADDRESS']           = self.VR_ADDRESS
                self.config['YOUTUBE_URL']          = self.YOUTUBE_URL
                self.config['CLOUD_URL_RTMP']       = self.CLOUD_URL_RTMP
                self.config['CLOUD_URL_RTMPS']      = self.CLOUD_URL_RTMPS

                stream.seek(0)
                stream.truncate()

                yaml.dump(self.config, stream=stream, default_flow_style=False, allow_unicode=True)
                stream.close()
            except yaml.YAMLError as exc:
                print(exc)
                



class System():
    username = None
    password = None
    
    PORT="/dev/ttyTHS0"
    BAUD_RATE=9600
    CAMERA_SETTINGS_WINDOW_SIZE_Y = None
    CAMERA_SETTINGS_WINDOW_SIZE_X = None

    system_file = "config/system.yaml"

    POWER_MODE=8

    SINGLE_CAM_OPERATION = False

    APPLICATION_SERVER_URL = "https://api.gioview.co.uk/api/v1"

    NVME_MOUNT_POINT = "/media/nvidia/GIOVIEW/"

    
    def __init__(self) -> None:

        
        yaml_path = "/config/system.yaml"
        print(yaml_path)

        self.system_file = dirname(dirname(dirname(abspath(__file__)))) + yaml_path if exists(dirname(dirname(dirname(abspath(__file__)))) + yaml_path) else dirname(dirname(abspath(__file__))) + yaml_path
        self.load()

        # print(dirname(dirname(abspath(__file__))), "happy")
        

    def load(self):
        with open(self.system_file, "r+") as stream:
            try:
                self.config = yaml.safe_load(stream)
                
                if 'PORT' in self.config:
                    self.PORT = self.config['PORT']

                if 'BAUD_RATE' in self.config:
                    self.BAUD_RATE = self.config['BAUD_RATE']

                if 'username' in self.config:
                    self.username = self.config['username']

                if 'password' in self.config:
                    self.password = self.config['password']

                if 'POWER_MODE' in self.config:
                    self.POWER_MODE = self.config['POWER_MODE']

                if 'SINGLE_CAM_OPERATION' in self.config:
                    self.SINGLE_CAM_OPERATION = self.config['SINGLE_CAM_OPERATION']

                if 'APPLICATION_SERVER_URL' in self.config:
                    self.APPLICATION_SERVER_URL = self.config['APPLICATION_SERVER_URL']

                if 'NVME_MOUNT_POINT' in self.config:
                    self.NVME_MOUNT_POINT = self.config['NVME_MOUNT_POINT']

                if 'ENABLE_CLOSE_APP_BUTTON' in self.config:
                    self.ENABLE_CLOSE_APP_BUTTON = self.config['ENABLE_CLOSE_APP_BUTTON']

                if 'NVME_PATH' in self.config:
                    self.NVME_PATH = self.config['NVME_PATH']

                if 'SNAPSTART' in self.config:
                    self.SNAPSTART = self.config['SNAPSTART']

                stream.close()

            except yaml.YAMLError as exc:
                print(exc)
  


    # def save(self):
    #     with open(self.camera_file, "r+") as stream:
    #         try:
    #             self.config['SNAPSTART']             = self.SNAPSTART

    #             stream.seek(0)
    #             stream.truncate()

    #             yaml.dump(self.config, stream=stream, default_flow_style=False, allow_unicode=True)
    #             stream.close()
    #         except yaml.YAMLError as exc:
    #             print(exc)
                



class UI():


    CAMERA_SETTINGS_WINDOW_SIZE_Y = None
    CAMERA_SETTINGS_WINDOW_SIZE_X = None

    system_file = "config/ui.yaml"

    ADMIN_IMAGE_SIZE=  '100,100'
    
    def __init__(self, screen_w:int=1528) -> None:

        if 1600<screen_w and screen_w<2200:
        # if screen_w<2200 and screen_w>1600:
        
            yaml_path = "/config/ui_7inch.yaml"

        elif screen_w > 2250:

            yaml_path = "/config/ui_14inch.yaml"

        # if screen_w<1600:
        #     yaml_path = "/config/ui.yaml"

        else :
            yaml_path = "/config/ui.yaml"

        # yaml_path = "/config/ui.yaml"
        print(yaml_path)

        self.system_file = dirname(dirname(dirname(abspath(__file__)))) + yaml_path if exists(dirname(dirname(dirname(abspath(__file__)))) + yaml_path) else dirname(dirname(abspath(__file__))) + yaml_path
        self.load()

        # print(dirname(dirname(abspath(__file__))), "happy")
        
    def load(self):
        with open(self.system_file, "r+") as stream:
            try:
                self.config = yaml.safe_load(stream)
                


                if 'ICON_SIZE' in self.config:
                    self.ICON_SIZE = self.config['ICON_SIZE']

                if 'CAMERA_SETTINGS_WINDOW_SIZE_X' in self.config:
                    self.CAMERA_SETTINGS_WINDOW_SIZE_X = self.config['CAMERA_SETTINGS_WINDOW_SIZE_X']

                if 'CAMERA_SETTINGS_WINDOW_SIZE_Y' in self.config:
                    self.CAMERA_SETTINGS_WINDOW_SIZE_Y = self.config['CAMERA_SETTINGS_WINDOW_SIZE_Y']

                if 'RIG_CONTROLLER_WINDOW_SIZE_X' in self.config:
                    self.RIG_CONTROLLER_WINDOW_SIZE_X = self.config['RIG_CONTROLLER_WINDOW_SIZE_X']

                if 'RIG_CONTROLLER_WINDOW_SIZE_Y' in self.config:
                    self.RIG_CONTROLLER_WINDOW_SIZE_Y = self.config['RIG_CONTROLLER_WINDOW_SIZE_Y']

                if 'MAIN_WINDOW_SIZE_Y' in self.config:
                    self.MAIN_WINDOW_SIZE_Y = self.config['MAIN_WINDOW_SIZE_Y']

                if 'SETTINGS_WINDOW_SIZE_X' in self.config:
                    self.SETTINGS_WINDOW_SIZE_X = self.config['SETTINGS_WINDOW_SIZE_X']

                if 'SETTINGS_WINDOW_SIZE_Y' in self.config:
                    self.SETTINGS_WINDOW_SIZE_Y = self.config['SETTINGS_WINDOW_SIZE_Y']

                if 'KEY_WINDOW_SIZE_X' in self.config:
                    self.KEY_WINDOW_SIZE_X = self.config['KEY_WINDOW_SIZE_X']

                if 'KEY_WINDOW_SIZE_Y' in self.config:
                    self.KEY_WINDOW_SIZE_Y = self.config['KEY_WINDOW_SIZE_Y']

                if 'STREAM_WINDOW_SIZE_X' in self.config:
                    self.STREAM_WINDOW_SIZE_X = self.config['STREAM_WINDOW_SIZE_X']

                if 'STREAM_WINDOW_SIZE_Y' in self.config:
                    self.STREAM_WINDOW_SIZE_Y = self.config['STREAM_WINDOW_SIZE_Y']

                if 'STREAM_WINDOW_MIN_X' in self.config:
                    self.STREAM_WINDOW_MIN_X = self.config['STREAM_WINDOW_MIN_X']

                if 'STREAM_WINDOW_MIN_Y' in self.config:
                    self.STREAM_WINDOW_MIN_Y = self.config['STREAM_WINDOW_MIN_Y']

                if 'TIMER_SIZE' in self.config:
                    self.TIMER_SIZE = self.config['TIMER_SIZE']

                if 'RECORD_WINDOW_SIZE_X' in self.config:
                    self.RECORD_WINDOW_SIZE_X = self.config['RECORD_WINDOW_SIZE_X']

                if 'RECORD_WINDOW_SIZE_Y' in self.config:
                    self.RECORD_WINDOW_SIZE_Y = self.config['RECORD_WINDOW_SIZE_Y']

                if 'DIAL_SIZE' in self.config:
                    self.DIAL_SIZE = self.config['DIAL_SIZE']

                if 'GALLERY_WINDOW_SIZE_X' in self.config:
                    self.GALLERY_WINDOW_SIZE_X = self.config['GALLERY_WINDOW_SIZE_X']

                if 'GALLERY_WINDOW_SIZE_Y' in self.config:
                    self.GALLERY_WINDOW_SIZE_Y = self.config['GALLERY_WINDOW_SIZE_Y']

                if 'PRESET_WINDOW_SIZE_X' in self.config:
                    self.PRESET_WINDOW_SIZE_X = self.config['PRESET_WINDOW_SIZE_X']

                if 'PRESET_WINDOW_SIZE_Y' in self.config:
                    self.PRESET_WINDOW_SIZE_Y = self.config['PRESET_WINDOW_SIZE_Y']

                if 'SELECT_3D_PREVIEW_WINDOW_X' in self.config:
                    self.SELECT_3D_PREVIEW_WINDOW_X = self.config['SELECT_3D_PREVIEW_WINDOW_X']

                if 'SELECT_3D_PREVIEW_WINDOW_Y' in self.config:
                    self.SELECT_3D_PREVIEW_WINDOW_Y = self.config['SELECT_3D_PREVIEW_WINDOW_Y']

                if 'AI_WINDOW_SIZE_X' in self.config:
                    self.AI_WINDOW_SIZE_X = self.config['AI_WINDOW_SIZE_X']

                if 'AI_WINDOW_SIZE_Y' in self.config:
                    self.AI_WINDOW_SIZE_Y = self.config['AI_WINDOW_SIZE_Y']

                if 'MEDIA_WINDOW_SIZE' in self.config:
                    self.MEDIA_WINDOW_SIZE = self.config['MEDIA_WINDOW_SIZE']

                if 'ADMIN_IMAGE_SIZE' in self.config:
                    self.ADMIN_IMAGE_SIZE = self.config['ADMIN_IMAGE_SIZE']

                if 'STREAM_TEST_WINDOW_SIZE' in self.config:
                    self.STREAM_TEST_WINDOW_SIZE = self.config['STREAM_TEST_WINDOW_SIZE']

                if 'BACKGROUNG_IMAGE' in self.config:
                    self.BACKGROUNG_IMAGE = self.config['BACKGROUNG_IMAGE']

                if 'DEVICE_SETTINGS_WINDOW_SIZE' in self.config:
                    self.DEVICE_SETTINGS_WINDOW_SIZE = self.config['DEVICE_SETTINGS_WINDOW_SIZE']

                stream.close()

            except yaml.YAMLError as exc:
                print(exc)
  

    def save(self):
        with open(self.system_file, "r+") as stream:
            try:
                self.config['ICON_SIZE']             = self.ICON_SIZE
                self.config['CAMERA_SETTINGS_WINDOW_SIZE_X']= self.CAMERA_SETTINGS_WINDOW_SIZE_X
                self.config['CAMERA_SETTINGS_WINDOW_SIZE_Y']= self.CAMERA_SETTINGS_WINDOW_SIZE_Y
                self.config['RIG_CONTROLLER_WINDOW_SIZE_X'] = self.RIG_CONTROLLER_WINDOW_SIZE_X
                self.config['RIG_CONTROLLER_WINDOW_SIZE_Y'] = self.RIG_CONTROLLER_WINDOW_SIZE_Y
                self.config['MAIN_WINDOW_SIZE_Y']           = self.MAIN_WINDOW_SIZE_Y
                self.config['SETTINGS_WINDOW_SIZE_X']       = self.SETTINGS_WINDOW_SIZE_X
                self.config['SETTINGS_WINDOW_SIZE_Y']       = self.SETTINGS_WINDOW_SIZE_Y
                self.config['KEY_WINDOW_SIZE_X']            = self.KEY_WINDOW_SIZE_X
                self.config['KEY_WINDOW_SIZE_Y']            = self.KEY_WINDOW_SIZE_Y
                self.config['STREAM_WINDOW_SIZE_X']         = self.STREAM_WINDOW_SIZE_X
                self.config['STREAM_WINDOW_SIZE_Y']         = self.STREAM_WINDOW_SIZE_Y
                self.config['STREAM_WINDOW_MIN_X']          = self.STREAM_WINDOW_MIN_X
                self.config['STREAM_WINDOW_MIN_Y']          = self.STREAM_WINDOW_MIN_Y
                self.config['TIMER_SIZE']                   = self.TIMER_SIZE
                self.config['RECORD_WINDOW_SIZE_X']         = self.RECORD_WINDOW_SIZE_X
                self.config['RECORD_WINDOW_SIZE_Y']         = self.RECORD_WINDOW_SIZE_Y
                self.config['DIAL_SIZE']                    = self.DIAL_SIZE
                self.config['GALLERY_WINDOW_SIZE_X']        = self.GALLERY_WINDOW_SIZE_X
                self.config['GALLERY_WINDOW_SIZE_Y']        = self.GALLERY_WINDOW_SIZE_Y
                self.config['PRESET_WINDOW_SIZE_X']         = self.PRESET_WINDOW_SIZE_X
                self.config['PRESET_WINDOW_SIZE_Y']         = self.PRESET_WINDOW_SIZE_Y
                self.config['SELECT_3D_PREVIEW_WINDOW_X']   = self.SELECT_3D_PREVIEW_WINDOW_X
                self.config['SELECT_3D_PREVIEW_WINDOW_Y']   = self.SELECT_3D_PREVIEW_WINDOW_Y
                self.config['AI_WINDOW_SIZE_Y']             = self.AI_WINDOW_SIZE_Y
                self.config['AI_WINDOW_SIZE_X']             = self.AI_WINDOW_SIZE_X
                self.config['MEDIA_WINDOW_SIZE']            = self.MEDIA_WINDOW_SIZE
                self.config['STREAM_TEST_WINDOW_SIZE']      = self.STREAM_TEST_WINDOW_SIZE
                self.config['DEVICE_SETTINGS_WINDOW_SIZE']  = self.DEVICE_SETTINGS_WINDOW_SIZE
    

                stream.seek(0)
                stream.truncate()

                yaml.dump(self.config, stream=stream, default_flow_style=False, allow_unicode=True)
                stream.close()
            except yaml.YAMLError as exc:
                print(exc)



class CameraSettings():

    WBMODE = 1
    AEANTI_BANDING = 1
    EDGE_ENHANCE = None
    AWB_LOCK = None
    AE_LOCK = None
    EXPOSURE_COMPENSATION = None
    SATURATION = None

    file = "config/cameraSettings.yaml"

    def __init__(self) -> None:
        
        # self.file = dirname(dirname(abspath(__file__))) + "/cameraSettings.yaml"
        self.file = dirname(dirname(dirname(abspath(__file__)))) + "/config/cameraSettings.yaml" if exists(dirname(dirname(dirname(abspath(__file__)))) + "/config/cameraSettings.yaml") else dirname(dirname(abspath(__file__))) + "/config/cameraSettings.yaml"
    #     
        self.load()
        pass

    def load(self):

        with open(self.file, "r+") as stream:
            try:
                self.config = yaml.safe_load(stream)

                if 'WBMODE' in self.config:
                    self.WBMODE = self.config['WBMODE']

                if 'AEANTI_BANDING' in self.config:
                    self.AEANTI_BANDING = self.config['AEANTI_BANDING']

                if 'EDGE_ENHANCE' in self.config:
                    self.EDGE_ENHANCE = self.config['EDGE_ENHANCE']

                if 'AWB_LOCK' in self.config:
                    self.AWB_LOCK = self.config['AWB_LOCK']

                if 'AE_LOCK' in self.config:
                    self.AE_LOCK = self.config['AE_LOCK']
                
                if 'EXPOSURE_COMPENSATION' in self.config:
                    self.EXPOSURE_COMPENSATION = self.config['EXPOSURE_COMPENSATION']

                if 'SATURATION' in self.config:
                    self.SATURATION = self.config['SATURATION']

                if 'TNR_MODE' in self.config:
                    self.TNR_MODE = self.config['TNR_MODE']


                if 'WBMODE_DEFAULT' in self.config:
                    self.WBMODE_DEFAULT = self.config['WBMODE_DEFAULT']

                if 'AEANTI_BANDING_DEFAULT' in self.config:
                    self.AEANTI_BANDING_DEFAULT = self.config['AEANTI_BANDING_DEFAULT']

                if 'EDGE_ENHANCE_DEFAULT' in self.config:
                    self.EDGE_ENHANCE_DEFAULT = self.config['EDGE_ENHANCE_DEFAULT']

                if 'AWB_LOCK_DEFAULT' in self.config:
                    self.AWB_LOCK_DEFAULT = self.config['AWB_LOCK_DEFAULT']

                if 'EXPOSURE_COMPENSATION_DEFAULT' in self.config:
                    self.EXPOSURE_COMPENSATION_DEFAULT = self.config['EXPOSURE_COMPENSATION_DEFAULT']

                if 'SATURATION_DEFAULT' in self.config:
                    self.SATURATION_DEFAULT = self.config['SATURATION_DEFAULT']

                if 'TNR_MODE_DEFAULT' in self.config:
                    self.TNR_MODE_DEFAULT = self.config['TNR_MODE_DEFAULT']

                

            except yaml.YAMLError as exc:
                print(exc)
    


    def save(self):
        
        with open(self.file, "r+") as stream:
            try:

                self.config['WBMODE']                   = self.WBMODE
                self.config['AEANTI_BANDING']           = self.AEANTI_BANDING
                self.config['EDGE_ENHANCE']             = self.EDGE_ENHANCE
                self.config['AWB_LOCK']                 = self.AWB_LOCK
                self.config['AE_LOCK']                  = self.AE_LOCK
                self.config['EXPOSURE_COMPENSATION']    = self.EXPOSURE_COMPENSATION
                self.config['SATURATION']               = self.SATURATION
                self.config['TNR_MODE']                 = self.TNR_MODE

                stream.seek(0)
                stream.truncate()

                yaml.dump(self.config, stream=stream, default_flow_style=False, allow_unicode=True)
                stream.close()
            except yaml.YAMLError as exc:
                print(exc)





class AISettings():
    MOTORS_BIDIRECTIONAL=False
    CROP_WINDOW_HEIGHT = 200
    CROP_WINDOW_WIDTH = 200

    file = "config/ai.yaml"

    def __init__(self) -> None:
        
        # self.file = dirname(dirname(abspath(__file__))) + "/cameraSettings.yaml"
        self.file = dirname(dirname(dirname(abspath(__file__)))) + "/config/ai.yaml" if exists(dirname(dirname(dirname(abspath(__file__)))) + "/config/ai.yaml") else dirname(dirname(abspath(__file__))) + "/config/ai.yaml"
    #     
        self.load()
        pass

    def load(self):
        
        with open(self.file, "r+") as stream:
            try:
                self.config = yaml.safe_load(stream)

                if 'CROP_WINDOW_HEIGHT' in self.config:
                    self.CROP_WINDOW_HEIGHT = self.config['CROP_WINDOW_HEIGHT']

                if 'CROP_WINDOW_WIDTH' in self.config:
                    self.CROP_WINDOW_WIDTH = self.config['CROP_WINDOW_WIDTH']

                if 'FRAME_HEIGHT' in self.config:
                    self.FRAME_HEIGHT = self.config['FRAME_HEIGHT']

                if 'FRAME_WIDTH' in self.config:
                    self.FRAME_WIDTH = self.config['FRAME_WIDTH']

                if 'SET_POINT' in self.config:
                    self.SET_POINT = self.config['SET_POINT']

                if 'VCALIB_DIRECTION' in self.config:
                    self.VCALIB_DIRECTION = self.config['VCALIB_DIRECTION']

                if 'HCALIB_DIRECTION' in self.config:
                    self.HCALIB_DIRECTION = self.config['HCALIB_DIRECTION']

                if 'CHANGE_3D_LEVEL' in self.config:
                    self.CHANGE_3D_LEVEL = self.config['CHANGE_3D_LEVEL']

            except yaml.YAMLError as exc:
                print(exc)
    



class StreamSettings():

    FPS_4K=30

    file = "config/stream.yaml"

    def __init__(self) -> None:
        
        # self.file = dirname(dirname(abspath(__file__))) + "/cameraSettings.yaml"
        self.file = dirname(dirname(dirname(abspath(__file__)))) + "/config/stream.yaml" if exists(dirname(dirname(dirname(abspath(__file__)))) + "/config/stream.yaml") else dirname(dirname(abspath(__file__))) + "/config/stream.yaml"
    #     
        self.load()
        pass

    def load(self):
        
        with open(self.file, "r+") as stream:
            try:
                self.config = yaml.safe_load(stream)

                if 'FPS_4K' in self.config:
                    self.FPS_4K = self.config['FPS_4K']

                if 'FPS_FHD' in self.config:
                    self.FPS_FHD = self.config['FPS_FHD']
                

            except yaml.YAMLError as exc:
                print(exc)
    





class AudioSettings():


    file = "config/audio.yaml"

    def __init__(self) -> None:
        
        # self.file = dirname(dirname(abspath(__file__))) + "/cameraSettings.yaml"
        self.file = dirname(dirname(dirname(abspath(__file__)))) + "/config/audio.yaml" if exists(dirname(dirname(dirname(abspath(__file__)))) + "/config/audio.yaml") else dirname(dirname(abspath(__file__))) + "/config/audio.yaml"
    #     
        self.load()
        pass

    def load(self):
        
        with open(self.file, "r+") as stream:
            try:
                self.config = yaml.safe_load(stream)

                if 'AUDIO_INPUT_DEVICE' in self.config:
                    self.AUDIO_INPUT_DEVICE = self.config['AUDIO_INPUT_DEVICE']

                if 'SYSTEM_AUDIO_INPUT' in self.config:
                    self.SYSTEM_AUDIO_INPUT = self.config['SYSTEM_AUDIO_INPUT']


            except yaml.YAMLError as exc:
                print(exc)
    
    # def save(self):
    #     with open(self.system_file, "r+") as stream:
    #         try:
    #             self.config['ICON_SIZE']             = self.ICON_SIZE

    #             stream.seek(0)
    #             stream.truncate()

    #             yaml.dump(self.config, stream=stream, default_flow_style=False, allow_unicode=True)
    #             stream.close()
    #         except yaml.YAMLError as exc:
    #             print(exc)










import json

class MotorPresets():

    presets = None

    file = "config/preset.yaml"

    def __init__(self) -> None:
        
        # self.file = dirname(dirname(abspath(__file__))) + "/preset.yaml"
        self.file = dirname(dirname(dirname(abspath(__file__)))) + "/config/preset.yaml" if exists(dirname(dirname(dirname(abspath(__file__)))) + "/config/preset.yaml") else dirname(dirname(abspath(__file__))) + "/config/preset.yaml"
    #     
        self.load()
        pass


    def load(self):
        with open(self.file, "r+") as file:
            try:
                self.presets = yaml.safe_load(file)

                # print(self.presets)

            except yaml.YAMLError as exc:
                print(exc)













    # def __init__(self) -> None:
    #     self.system_file = dirname(dirname(dirname(abspath(__file__)))) + "/system.yaml" if exists(dirname(dirname(dirname(abspath(__file__)))) + "/system.yaml") else dirname(dirname(abspath(__file__))) + "/system.yaml"
    #     self.load()

    #     print(dirname(dirname(abspath(__file__))), "happy")
        
    # def load(self):
    #     with open(self.system_file, "r+") as stream:
    #         try:
    #             self.config = yaml.safe_load(stream)
                
    #             if 'PORT' in self.config:
    #                 self.PORT = self.config['PORT']
    #             if 'BAUD_RATE' in self.config:
    #                 self.BAUD_RATE = self.config['BAUD_RATE']

            


    # def save(self):
    #     with open(self.camera_file, "r+") as stream:
    #         try:
    #             self.config['SOURCE_L']             = self.SOURCE_L
    #             self.config['SOURCE_R']             = self.SOURCE_R
    #             self.config['FRAME_WIDTH']          = self.FRAME_WIDTH
    #             self.config['FRAME_HEIGHT']         = self.FRAME_HEIGHT
    #             self.config['DROP_LOCATION']        = self.DROP_LOCATION
    #             self.config['YOUTUBE_STREAM_KEY']   = self.YOUTUBE_STREAM_KEY
    #             self.config['CLOUD_STREAM_KEY']     = self.CLOUD_STREAM_KEY
    #             self.config['VR_ADDRESS']           = self.VR_ADDRESS
    #             self.config['YOUTUBE_URL']          = self.YOUTUBE_URL
    #             self.config['CLOUD_URL']            = self.CLOUD_URL

    #             stream.seek(0)
    #             stream.truncate()

    #             yaml.dump(self.config, stream=stream, default_flow_style=False, allow_unicode=True)
    #             stream.close()
    #         except yaml.YAMLError as exc:
    #             print(exc)
                