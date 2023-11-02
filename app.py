

# from logging.config import valid_ident
import sys, os
import multiprocessing
from controls.motor import MotorParameters
import subprocess
import queue
import time
import glob
import os.path
import re
from threading import Timer
import shutil
import queue
from time import sleep
from PyQt5 import QtGui
import threading
from pynput import keyboard
# import base64
import pika


# Qt5 necessary imports
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication,QFileDialog
# from PyQt5.QtGui import QFont
# from PyQt5.QtGui import QColor
# from PyQt5.QtCore import pyqtSignal
# application specific module imports
# from controls.settings import Camera, System, CameraSettings, MotorPresets, AISettings
from controls.camera import CameraParameters
from controls.callbacks import TimerCallbacks
from Main_Pipeline import CameraStreamer
from PyQt5 import uic

import requests
import xml.etree.ElementTree as ET
from PyQt5.QtCore import Qt
import cv2
import numpy as np
import pandas as pd
from threading import Timer

import sys

import pygame

from pygame.locals import*
import paho.mqtt.client as mqtt

# from controls import mqtt

# import startup

# from controls.remotecontrol import RemoteControler


#        Global Variables 
#-------------------------------
    

# for stream
# -------------------

STREAM_KEY = None
CURRENT_PREVIEW = "stich"

# for login
#--------------------

LOGIN_STATE = 0
DISPLAY_USERNAME = None
ADMIN_IMAGE = None


# for recording

PLAYING_STATE = False
PLAY_STOP = False


MAIN_WINDOW_CLICKABLE = True


uifile_1 = 'ui/home-window.ui'
form_1, base_1 = uic.loadUiType(uifile_1)

uifile_3 = 'ui/Recording-window.ui'
form_3, base_3 = uic.loadUiType(uifile_3)

uifile_4 = 'ui/liveStream-window.ui'
form_4, base_4 = uic.loadUiType(uifile_4)

uifile_5 = 'ui/streamkey-window.ui'
form_5, base_5 = uic.loadUiType(uifile_5)

uifile_9 = 'ui/Settings-window.ui'
form_9, base_9 = uic.loadUiType(uifile_9)

uifile_10 = 'ui/RigControl-window.ui'
form_10, base_10 = uic.loadUiType(uifile_10)

uifile_11 = 'ui/RecordingFolder.ui'
form_11, base_11 = uic.loadUiType(uifile_11)

uifile_13 = 'ui/fileManage-window.ui'
form_13, base_13 = uic.loadUiType(uifile_13)

uifile_14 = 'ui/FileMove-window.ui'
form_14, base_14 = uic.loadUiType(uifile_14)

uifile_15 = 'ui/background-window.ui'
form_15, base_15 = uic.loadUiType(uifile_15)

uifile_16 = 'ui/exit-window.ui'
form_16, base_16 = uic.loadUiType(uifile_16)

uifile_17 = 'ui/camera-settings-window.ui'
form_17, base_17 = uic.loadUiType(uifile_17)

uifile_19 = 'ui/videoPlayer-window.ui'
form_19, base_19 = uic.loadUiType(uifile_19)

uifile_20 = 'ui/presets-window.ui'
form_20, base_20 = uic.loadUiType(uifile_20)

uifile_21 = 'ui/preview-window.ui'
form_21, base_21 = uic.loadUiType(uifile_21)

uifile_22 = 'ui/AI-window.ui'
form_22, base_22 = uic.loadUiType(uifile_22)

uifile_23 = 'ui/p2p-window.ui'
form_23, base_23 = uic.loadUiType(uifile_23)

uifile_24 = 'ui/media-window.ui'
form_24, base_24 = uic.loadUiType(uifile_24)

uifile_25 = 'ui/videoEditor-window.ui'
form_25, base_25 = uic.loadUiType(uifile_25)

uifile_26 = 'ui/streamTest-window.ui'
form_26, base_26 = uic.loadUiType(uifile_26)

uifile_27 = 'ui/device_settings_window.ui'
form_27, base_27 = uic.loadUiType(uifile_27)


# read base directory
# basedir = os.path.dirname(__file__)

# define shutdown hook
def system_shudown_hook(exctype, value, traceback):
	for p in multiprocessing.active_children():
		p.terminate()


class MainWindow(base_1, form_1):

    def __init__(self, pipeline, motors):
        super(base_1,self).__init__()
        self.setupUi(self)      
        self.sys = systemConfig
        self.cam = systemCamera
        self.ui = systemUI
        self.audio = audioConfig
    
        self.mainWindowHeight = self.ui.MAIN_WINDOW_SIZE_Y
        self.resize((screen_width),self.mainWindowHeight)
    
        self.pipeline = pipeline
        self.motors = motors

        self.processTimer = Timer

        self.setEnabled(False)

        # Set button Actions

        try :

            self.buttonStream.clicked.connect(self.openStreamWindow)
            self.buttonRecord.clicked.connect(self.openRecordingWindow)
            self.buttonSettingsMainWindow.clicked.connect(self.openSettingsMainWindow)
            self.buttonBarrelCorrection.clicked.connect(self.openButtonBarrelCorrection)
            self.buttonGallery.clicked.connect(self.buttonGalleryAction)
            self.buttoncloseMainWindow.clicked.connect(self.openConfirmWindow)
            self.buttonLocalStream.clicked.connect(self.buttonLocalStreamClickAction)
            self.button3D.clicked.connect(self.button3DClickAction)
            self.buttonZeroPoint.clicked.connect(self.buttonAI_ClickedAction)
            self.buttonTestStream.clicked.connect(self.buttonTestStream_clickAction)
        
            # Set icon sizes
            self.buttonStream.setIconSize(ICON_SIZE)
            self.buttonRecord.setIconSize(ICON_SIZE)
            self.buttonGallery.setIconSize(ICON_SIZE)
            self.buttonSettingsMainWindow.setIconSize(ICON_SIZE)
            self.buttoncloseMainWindow.setIconSize(ICON_SIZE)
            self.buttonBarrelCorrection.setIconSize(ICON_SIZE)
            self.buttonZeroPoint.setIconSize(ICON_SIZE)
            self.buttonLocalStream.setIconSize(ICON_SIZE)
            self.button3D.setIconSize(ICON_SIZE)
            self.buttonTestStream.setIconSize(ICON_SIZE)
        
        except:

            print("**Check all buttons are in the ui")


        self.pipeline.apply_shader=False

    
        # DISABLE BUTTONS FOR SINGLE CAM OPERATION
        if self.sys.SINGLE_CAM_OPERATION:
            # self.buttonPreview3D.hide()
            # self.buttonPreviewBlend.hide()
            self.buttonPreviewRight.hide()

        #------------------------------------------------------------
        self.openBlackWindow()

        subprocess.call(["echo {0} | sudo -S chmod o+rw {1}".format(self.sys.password, self.sys.PORT)], shell=True)
        subprocess.call(["echo {0} | sudo -S stty {1} -F {2}".format(self.sys.password, self.sys.BAUD_RATE, self.sys.PORT)], shell=True)
        subprocess.call(["echo {0} | sudo -S systemctl restart nvargus-daemon".format(self.sys.password)], shell=True)
              
        self.mountExternalDrive()
        self.desableButtons()

        if self.sys.SNAPSTART==True:

            self.OpenSBSPreviewAtStartup()

            time.sleep(5)

        self.setEnabled(True)
        self.changeSystemMicInput()
        # nvgstcapture-1.0 --image-res=8 --file-name=/home/giocam3d/captured_image -m 1 --capture-auto
#


    def OpenSBSPreviewAtStartup(self): # delay 0.5 seconds . otherwise error occure
        def sss():
            self.previewStart()
        t = self.processTimer(1 ,sss)
        t.start()

    def previewStart(self):

        try:


            self.pipeline.stop_preview()
            sleep(2)

            self.pipeline.sideBysidePreview()

            

        except:

            print("Unable to start preview at startup")



    def desableButtons(self):

        # xmodmap -pke | grep -i "Super"
            # keycode 133 = Super_L NoSymbol Super_L
            # keycode 134 = Super_R NoSymbol Super_R
            # keycode 206 = NoSymbol Super_L NoSymbol Super_L

        try:

            output = subprocess.run(['xmodmap', '-e', 'keycode 133 = '], capture_output=True)

            # Print the output of the command
            print(output.stdout)

            print("Super Button Deactivated")

        except:
            print("Deactivate Super button Failed")

    def mountExternalDrive(self):

        drive_path = self.sys.NVME_PATH
        mount_point = self.sys.NVME_MOUNT_POINT


        try:
            subprocess.check_output(['sudo', 'mount', drive_path, mount_point])
            print(f"Drive {drive_path} mounted at {mount_point}")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            

        # ''''''''''''''''''''''''''''''''''''
        # def unmount_external_drive(mount_point):
        #     try:
        #         subprocess.check_output(['sudo', 'umount', mount_point])
        #         print(f"Drive at {mount_point} unmounted")
        #     except subprocess.CalledProcessError as e:
        #         print(f"Error: {e}")
        # '''''''''''''''''''''''''''''''''''''''''

        pass

        
    def buttonTestStream_clickAction(self):

        self.windowTestStream = StreamTest(cm, mp)
        self.windowTestStream.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.windowTestStream.setWindowFlags(self.windowTestStream.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.windowTestStream.setWindowTitle('Stream Test')
        self.windowTestStream.show()


    def buttonAI_ClickedAction(self):

        self.windowSelectPreview = AiWindow(cm, mp)
        self.windowSelectPreview.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.windowSelectPreview.setWindowFlags(self.windowSelectPreview.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.windowSelectPreview.setWindowTitle('Auto Calibration')
        self.hide()
        self.windowSelectPreview.show()
        

    def button3DClickAction(self):

        self.windowSelectPreview = Select3DPreview(cm)
        self.windowSelectPreview.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.windowSelectPreview.setWindowFlags(self.windowSelectPreview.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.windowSelectPreview.setWindowTitle('3D View Mode')
        # self.close()
        self.windowSelectPreview.show()


    def buttonGalleryAction(self):
        self.media_Window = MediaWindow(cm)
        self.media_Window.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.media_Window.setWindowFlags(self.media_Window.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.media_Window.setWindowTitle(' Media ')
        self.hide()
        self.media_Window.show()


    def buttonLocalStreamClickAction(self):

        self.p2p_Window = P2PWindow(cm,  mp)
        self.p2p_Window.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.p2p_Window.setWindowFlags(self.p2p_Window.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.p2p_Window.setWindowTitle(' Peer to Peer ')
        self.hide()
        self.p2p_Window.show()

        pass
    
    def openRecordingWindow(self):
        global MAIN_WINDOW_CLICKABLE

        if MAIN_WINDOW_CLICKABLE is True:
        # pm = PipelineMaster()
            self.window = recordWindow(cm)
            self.window.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
            self.window.setWindowFlags(self.window.windowFlags() & ~Qt.WindowCloseButtonHint)
            self.window.setWindowTitle(' ')
            self.hide()
            self.window.show()
    


    def openButtonBarrelCorrection(self):

        global CURRENT_PREVIEW
        state=False

        if self.buttonBarrelCorrection.isChecked():
            state=True
        self.pipeline.apply_shader=state

    def resizeEvent(self, event):

        window_size = self.size()

        self.mainWindowHeight = window_size.height()
        self.saveWindowSize()

    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Store the initial mouse position and window position
            self.startPos = event.globalPos()
            self.windowPos = self.frameGeometry().topLeft()


    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # Calculate the new window position based on the mouse movement
            delta = event.globalPos() - self.startPos
            self.move(self.windowPos + delta)


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Clear the stored positions
            self.startPos = None
            self.windowPos = None




    def buttonGroupSelectCameraModeClickAction(self, button):

        global MAIN_WINDOW_CLICKABLE
        global CURRENT_PREVIEW

        state=False                  

        if self.buttonBarrelCorrection.isChecked():
            state=True

        self.pipeline.apply_shader=state

        if button.objectName().__eq__("buttonPreviewLeft"):

            if MAIN_WINDOW_CLICKABLE is True:
                CURRENT_PREVIEW="left"
                self.pipeline.stop_preview()
                sleep(2)
                self.pipeline.leftCameraPreview()

        if button.objectName().__eq__("buttonPreviewRight"):
            
            if MAIN_WINDOW_CLICKABLE is True:
                CURRENT_PREVIEW = "right"
                self.pipeline.stop_preview()
                sleep(2)
                self.pipeline.rightCameraPreview()




    def saveWindowSize(self):

        self.ui.MAIN_WINDOW_SIZE_Y = self.mainWindowHeight
        self.ui.save()


    def openConfirmWindow(self):
        if hasattr(self.pipeline, 'pipeline') and self.pipeline.pipeline is not None:
            # self.pipeline.stop_recording()
            self.pipeline.stop_preview()
            # subprocess.call(["echo {0} | sudo -S systemctl restart nvargus-daemon".format(self.sys.password)], shell=True)
        else:
            self.window = ExitConfirmWindow(cm)
            self.window.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.hide()
            self.window.resize(int(screen_width/3),int(screen_height/3))
            self.window.show()

    def openSettingsMainWindow(self):
        self.settingsWindow = SettingsPage()
        # self.settingsWindow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.settingsWindow.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.settingsWindow.setWindowFlags(self.settingsWindow.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.settingsWindow.setWindowTitle(' ')
        # self.hide()
        self.settingsWindow.show()


    def videoQualityCheckBoxClickedAction(self):
        self.pipeline.rec_4k    = True  if self.videoQualityCheckBox.isChecked() else False
        
        self.pipeline.cap_fps 	= 30    if self.pipeline.rec_4k else 30 #50
        self.pipeline.cap_width	= 3840  if self.pipeline.rec_4k else 1920
        self.pipeline.cap_height= 2160  if self.pipeline.rec_4k else 1080


    def openStreamWindow(self):

        global MAIN_WINDOW_CLICKABLE

        if MAIN_WINDOW_CLICKABLE is True:

            self.window = StreamWindow(cm)
            self.window.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
            self.window.setWindowFlags(self.window.windowFlags() & ~Qt.WindowCloseButtonHint)
            self.window.setWindowTitle(' ')
            self.hide()
            self.window.show()

     

    def changeNameOfPreviewWindow(self):
        def yyy():
            self.renamePreviewWindow()
        y = self.processTimer(2.5 ,yyy)
        y.start()


    def renamePreviewWindow(self): # Rename preview Window
        
        try:
            cmd = "xdotool search --name app"
            output = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True).communicate()[0]
            # print(output.strip()) # For single line output.
            text = str(output)
            numbers_only = re.findall(r'\d+(?:\.\d+)?', text)
            window_id = int(numbers_only[0])
            os.system('xprop -id {0} -format _MOTIF_WM_HINTS 32a -set _MOTIF_WM_HINTS "0x2, 0x0, 0x0, 0x0, 0x0"'.format(window_id))
            os.system('xprop -id {0} -f WM_NAME 8s -set WM_NAME "python3"'.format(window_id))
        except:
            pass

    def openBlackWindow(self):
        self.blackWindow = BlackWindow()
        # self.blackWindow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self.blackWindow.setWindowFlags(Qt.FramelessWindowHint)
        # self.blackWindow.resize(screen_width,screen_height)
        self.blackWindow.show()


    def changeSystemMicInput(self):

        # pactl list short sources                     command to list
        source_name = self.audio.SYSTEM_AUDIO_INPUT

        try:
            # Runs the command to set the default source by name
            subprocess.run(['pactl', 'set-default-source', source_name], check=True)
            print(f"Default source set to: {source_name}")
        except subprocess.CalledProcessError as e:
            # This will catch any errors that the pactl command returns
            print(f"An error occurred: {e}")



class StreamTest(base_26, form_26):

    def __init__(self, pipeline, motors):
        super(base_26, self).__init__()
        self.setupUi(self)
        self.pipeline = pipeline
        self.ui = systemUI
        self.cam = systemCamera

        self.buttonStart.clicked.connect(self.startStream)
        self.buttonStop.clicked.connect(self.stopStream)
        self.buttonExittt.clicked.connect(self.buttonExittt_action)
        self.button4kMedialive.clicked.connect(self.button4kMedialive_action)
        self.button4kwowza.clicked.connect(self.button4kwowza_action)

        self.resizeWindow()

# 869853024695076
    def resizeWindow(self):

        size = self.ui.STREAM_TEST_WINDOW_SIZE
        w,h = size.split(',')
        self.resize(int(w),int(h))

    def resizeEvent(self, event):

        size = self.size()
        x = size.width()
        y = size.height()
        new_size = str(x)+","+str(y)
        self.ui.STREAM_TEST_WINDOW_SIZE = new_size
        self.ui.save()
        print(new_size)


    def startStream(self):

        self.buttonStart.setEnabled(False)
        self.button4kMedialive.setVisible(False)
        # self.buttonMedialiveH264.setVisible(False)
        self.button4kwowza.setVisible(False)
        self.buttonStop.setEnabled(True)
        self.buttonExittt.setEnabled(False)
        key = self.lineEdit.text()
        key = str(key.strip())
        self.pipeline.stop_preview()
        sleep(3)
        self.pipeline.stream_rtmp(stream_key=key)

        pass

    def button4kMedialive_action(self):

        bit_rate = int(self.lineEditBitrate.text())

        self.buttonStart.setVisible(False)
        # self.buttonMedialiveH264.setVisible(False)
        self.button4kMedialive.setEnabled(False)
        self.button4kwowza.setVisible(False)
        self.buttonStop.setEnabled(True)

        self.pipeline.stop_preview()
        sleep(3)
        # self.pipeline.stream_rtmp_4k()
        self.pipeline.stream_rtmp_4k(streamService='medialive', bitrate=bit_rate)
    
        pass

    def button4kwowza_action(self):

        self.buttonStart.setVisible(False)
        self.button4kMedialive.setVisible(False)
        # self.buttonMedialiveH264.setVisible(False)
        self.button4kwowza.setEnabled(False)
        self.buttonStop.setEnabled(True)
        self.buttonExittt.setEnabled(False)

        self.pipeline.stop_preview()
        sleep(3)
        self.pipeline.stream_rtmp_4k(streamService='wowza')


    def stopStream(self):
        self.buttonStart.setEnabled(True)
        self.button4kMedialive.setEnabled(True)
        self.button4kwowza.setEnabled(True)
        self.buttonStart.setVisible(True)
        self.button4kMedialive.setVisible(True)
        self.button4kwowza.setVisible(True)
        # self.buttonMedialiveH264.setVisible(True)
        # self.buttonMedialiveH264.setEnabled(True)
        self.buttonStop.setEnabled(False)
        self.buttonExittt.setEnabled(True)

        self.pipeline.stop_recording()

        pass

    def buttonExittt_action(self):

        self.close()
        windowHome.show()


class P2PWindow(base_23, form_23):

    pygame.init()

    pygame.joystick.init()

    abc=False
    deviceName = ""
    motorMotionState = None
    nu_of_steps = 1

    def __init__(self, pipeline, motors):
        super(base_23, self).__init__()
        self.setupUi(self)
        self.pipeline=pipeline
        self.motors = motors
        self.cam = systemCamera

        self.processTimer = Timer

        self.buttonP2P.clicked.connect(self.buttonP2PClickAction)
        self.buttonStopP2P.clicked.connect(self.buttonStopP2PAction)
        self.buttonExit.clicked.connect(self.closeEvent)

        self.buttonStart4K_p2p.clicked.connect(self.starrt4K)
        self.buttonStart4K_p2p.setVisible(False)

        self.buttonStopP2P.setVisible(False)

        #  Set icon sizes

        self.closeButton_previewWindow.setIconSize(ICON_SIZE*0.8)

        text = self.cam.VR_ADDRESS.strip()
        self.lineEditIpAddress.setText(text)

        self.stop_flag = threading.Event()
        self.mqtt_flag = threading.Event()
        self.rabbitmq_flag = threading.Event()

        self.thread()
        
        self.joysticks = self.add_remove_controllers()

        self.control_motor_left =1
        self.control_motor_right=6

        self.selected_motor = "LR"

        # self.mqtt_thread()
        self.rabbitmq_thread()
        self.motorAction()



        

    def motorAction(self):

        def sss():
            self.abc=True
        t = self.processTimer(4 ,sss)
        t.start()



    def mqttFunction(self):

        self.mqtt_broker_ip     = "139.162.50.185"
        self.mqtt_port          =  1883
        self.mqtt_username      = "kapraadmin"
        self.mqtt_password      = "kapraadmin"
        self.mqtt_topic         = "esp/ds18b20/temperature1"

        self.client = mqtt.Client()
        self.client.username_pw_set(username=self.mqtt_username, password=self.mqtt_password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.connect()
        self.start_mqtt_service()
        self.run_forever()

    



    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe(self.mqtt_topic)

    def on_message(self, client, userdata, msg):
        # decoded_msg = msg.payload.decode()

        base64_message = msg.payload.decode()
        # binary_message = base64.b64decode(base64_message)
        cmd = bytearray(base64_message)

        print(f"Received message on topic {msg.topic}: {base64_message}")

        self.motors.sendSerialCommand(cmd = cmd)



    def connect(self):
        self.client.connect(self.mqtt_broker_ip, self.mqtt_port, 60)

    def start_mqtt_service(self):
        self.client.loop_start()


    def run_forever(self):
        self.client.loop_start()
        try:
            while not self.mqtt_flag.is_set():
                pass
            self.client.disconnect()
            self.client.loop_stop()
        # except KeyboardInterrupt:
        except:
            # Gracefully exit on Ctrl+C
            print("Exiting the script.")
            # self.client.disconnect()
            # self.client.loop_stop()


    def starrt4K(self):
        IpAddress = self.lineEditIpAddress.text()
        self.pipeline.localStream2VR(vrIPAddress=IpAddress, quality="2160p")
        pass

        
    def add_remove_controllers(self):

        jss = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

        for js in jss:

            print(js.get_name())
            self.deviceName = js.get_name()

        return jss



    def buttonExitAction(self):

        self.close()
        windowHome.show()
        pass



    def buttonP2PClickAction(self):

        self.buttonP2P.setVisible(False)
        self.buttonStopP2P.setVisible(True)
        self.buttonExit.setVisible(False)
        self.lineEditIpAddress.setEnabled(False)

        IpAddress = self.lineEditIpAddress.text()
        

        self.pipeline.stop_preview()
        sleep(2)
        self.pipeline.localStream2VR(vrIPAddress=IpAddress)



    def buttonStopP2PAction(self):

        self.buttonP2P.setVisible(True)
        self.buttonStopP2P.setVisible(False)
        self.buttonExit.setVisible(True)
        self.lineEditIpAddress.setEnabled(True)

        self.pipeline.stop_preview()
        pass


    def thread(self):
        self.stop_flag.clear()
        self.threadProcess = threading.Thread(target=self.threadLoop)
        self.threadProcess.setDaemon
        self.threadProcess.start()

    def mqtt_thread(self):

        self.mqtt_flag.clear()
        self.mqtt_thread_process = threading.Thread(target=self.mqttFunction)
        self.mqtt_thread_process.setDaemon
        self.mqtt_thread_process.start()

    def rabbitmq_thread(self):
        self.rabbitmq_flag.clear()
        self.rabbit_thread_process = threading.Thread(target=self.rabbitmqFunction)
        self.rabbit_thread_process.setDaemon
        self.rabbit_thread_process.start()

    def rabbitmqFunction(self):
        
        # RabbitMQ server connection parameters
        rabbitmq_server = '172.104.54.240'  # Replace with the actual RabbitMQ server IP address
        rabbitmq_port = 5672  # Default RabbitMQ port
        rabbitmq_user = 'admin'  # Replace with your RabbitMQ username
        rabbitmq_password = 'admin'  # Replace with your RabbitMQ password
        vhost = 'vhosts'  # Replace with your RabbitMQ virtual host
        exchange_name = 'NadeejaD'  # Replace with the name of the existing exchange
        queue_name = 'NadeejaDQ'  # Replace with the name of the existing queue
        routing_key = 'all'  # Replace with your desired routing key

        # Create a connection to the RabbitMQ server
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
        
        parameters = pika.ConnectionParameters(
            host=rabbitmq_server,
            port=rabbitmq_port,
            virtual_host=vhost,
            credentials=credentials
        )

        self.rabbitMQ_connection = pika.BlockingConnection(parameters)
        self.rabbitMQ_channel = self.rabbitMQ_connection.channel()

        # Set up the message consumption callback
        def callback(ch, method, properties, body):
            message = body.decode()
            print(f"Received message: {message}")
            # time.sleep(2)

            if self.abc == True:

                self.createMsg(message=message)

            else:
                pass

        # Start consuming messages from the existing queue
        self.rabbitMQ_channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

        print(f"Waiting for messages from exchange '{exchange_name}' to queue '{queue_name}' with routing key '{routing_key}' on RabbitMQ server at {rabbitmq_server}. To exit, press Ctrl+C.")

        
        # Start consuming messages
        self.rabbitMQ_channel.start_consuming()

        # if old_msg == '2':
        #     self.rabbitMQ_channel.stop_consuming()
        #     self.abbitMQ_channel.close()
        # else:
        #     pass




    def createMsg(self, message):

        messages = message.split(',')
        print(messages)

        if len(messages) == 4:
            move_type, motor, direction, steps = messages[0], messages[1], messages[2], messages[3]   # C,L,CCW,5
            print("msg1:", move_type)
            print("msg2:", motor)
            print("msg3:", direction)
            print("msg4:", steps)
        else:
            print("Insufficient messages in the input.")

        
        if move_type == 'S':
            self.control_motor_left = 1
            self.control_motor_right = 6
        elif move_type == 'C':
            self.control_motor_left = 3
            self.control_motor_right = 4
        elif move_type == 'T':
            self.control_motor_left = 2
            self.control_motor_right = 5
        else:
            print("Invalide command")

        self.nu_of_steps = int(steps)
        self.selected_motor = motor


        if direction == 'CW':
            self.buttonmoveCWClick()
        elif direction == 'CCW':
            self.buttonmoveCCWClick()
        elif direction == 'HOME':
            self.buttonMoveHomeClickAction()
        elif direction == 'STOP':
            self.buttonMoveStopClickAction()
        else:
            print("Invalide command")
        




    def buttonmoveCWClick(self):
        # tilt 2, 5      con 3, 4            sep 1, 6

        
        direction = 1

        if self.selected_motor == "L":
            cmd = self.motors.move_steps(m1=self.control_motor_left, move=True, direction=direction, steps=self.nu_of_steps)

        elif self.selected_motor == "R":
            cmd = self.motors.move_steps(m1=self.control_motor_right, move=True, direction=direction, steps=self.nu_of_steps)
            pass

        else :
            cmd = self.motors.move_steps(m1=self.control_motor_left, m2=self.control_motor_right, move=True, direction=direction, steps=self.nu_of_steps)
            pass

        self.motors.sendSerialCommand(cmd = cmd)


    def buttonmoveCCWClick(self):

        direction = 0
    
        if self.selected_motor == "L":
            cmd = self.motors.move_steps(m1=self.control_motor_left, move=True, direction=direction, steps=self.nu_of_steps)
            pass

        elif self.selected_motor == "R":
            cmd = self.motors.move_steps(m1=self.control_motor_right, move=True, direction=direction, steps=self.nu_of_steps)
            pass

        else :
            cmd = self.motors.move_steps(m1=self.control_motor_left, m2=self.control_motor_right, move=True, direction=direction, steps=self.nu_of_steps)
            pass

        self.motors.sendSerialCommand(cmd = cmd)



    def buttonMoveHomeClickAction(self):

        

        if self.selected_motor == "L":
            cmd = self.motors.move_home(m1=self.control_motor_left)
            pass
        elif self.selected_motor == "R":
            cmd = self.motors.move_home(m1=self.control_motor_right)
            pass
        else :
            cmd = self.motors.move_home(m1=self.control_motor_left, m2=self.control_motor_right)
            pass

        self.motors.sendSerialCommand(cmd = cmd)



    def buttonMoveStopClickAction(self):

        if self.selected_motor == "L":
            cmd = self.motors.move_stop(m1=self.control_motor_left)
            pass
        elif self.selected_motor == "R":
            cmd = self.motors.move_stop(m1=self.control_motor_right)
            pass
        else :
            cmd = self.motors.move_stop(m1=self.control_motor_left, m2=self.control_motor_right)
            pass


        self.motors.sendSerialCommand(cmd = cmd)



    # def buttonmoveCWClickAction(self):
    
    #     if self.selected_motor == "L":
    #         cmd = self.motors.move_steps(m1=self.control_motor_left, move=True, direction=self.direction_of_motor, steps=self.nu_of_steps)

    #     elif self.selected_motor == "R":
    #         cmd = self.motors.move_steps(m1=self.control_motor_right, move=True, direction=self.direction_of_motor, steps=self.nu_of_steps)
    #         pass

    #     else :
    #         cmd = self.motors.move_steps(m1=self.control_motor_left, m2=self.control_motor_right, move=True, direction=self.direction_of_motor, steps=self.nu_of_steps)
    #         pass

    #     self.motors.sendSerialCommand(cmd = cmd)


    # def buttonmoveCCWClickAction(self):
    
    #     if self.selected_motor == "L":
    #         cmd = self.motors.move_steps(m1=self.control_motor_left, move=True, direction=self.direction_of_motor, steps=self.nu_of_steps)
    #         pass

    #     elif self.selected_motor == "R":
    #         cmd = self.motors.move_steps(m1=self.control_motor_right, move=True, direction=self.direction_of_motor, steps=self.nu_of_steps)
    #         pass

    #     else :
    #         cmd = self.motors.move_steps(m1=self.control_motor_left, m2=self.control_motor_right, move=True, direction=self.direction_of_motor, steps=self.nu_of_steps)
    #         pass

    #     self.motors.sendSerialCommand(cmd = cmd)



    def process_event(self, event):
        current_time = time.time()

        if current_time - self.last_event_time >= 0.5:  # 500 ms
            # Process the event
            print("Event processed:", event)

            # Update the last event time
            self.last_event_time = current_time
        
        pass


    def threadLoop(self):
        while not self.stop_flag.is_set():

            # print("thread is running")

            if self.motorMotionState == (-1, 0):
                self.direction_of_motor =   0
                self.buttonmoveCCWClickAction()
                pass

            if self.motorMotionState == (1, 0):
                self.direction_of_motor =   1
                self.buttonmoveCWClickAction()
                pass



            for event in pygame.event.get():
                
                # print(event)


                if event.type == JOYBUTTONUP:

                    print(event)


                if event.type == JOYHATMOTION:
                    
                    val = event.value
                    print(event)
                    print(val)

                    self.motorMotionState = val
                    pass

                    if val == (0,1):
                        self.nu_of_steps = min(self.nu_of_steps+1,10)
                        print(self.nu_of_steps)

                    if val == (0,-1):
                        self.nu_of_steps = max(self.nu_of_steps-1, 1)
                        print(self.nu_of_steps)

                if event.type == JOYAXISMOTION:

                    # print(event)
                    value = event.value
                    if event.axis ==2:
                        self.buttonmoveCCWClickAction()
                        self.direction_of_motor =   0
                        print("Move AntiClockwise", value)

                    if event.axis ==5:
                        self.buttonmoveCWClickAction()
                        self.direction_of_motor =   1
                        print("Move Clockwise", value)


                if event.type == JOYBUTTONDOWN:

                    # print(event)

                    if event.button == 0:

                        print("PRESSED A:", event.button)


                    
                    if event.button == 2:

                        print("Seperation Move Selected")
                        self.control_motor_left =1
                        self.control_motor_right=6

                    if event.button == 3:

                        print("Convergence Move Selected")
                        self.control_motor_left =2
                        self.control_motor_right=5

                    if event.button == 1:

                        print("Tilt Move Selected")
                        self.control_motor_left =3
                        self.control_motor_right=4


                    if event.button == 6:

                        print("Left Motor Selected")
                        self.selected_motor = "L"

                    if event.button == 7:

                        print("Right Motor Selected")
                        self.selected_motor = "R"

                    if event.button == 8:

                        print("Both Motors Selected")
                        self.selected_motor = "LR"



                if event.type == JOYDEVICEADDED:

                    self.joysticks = self.add_remove_controllers()
                    
                    txt=f"{self.deviceName} Connected"

                    print(txt)
                    self.labelStatus.setStyleSheet("color: lightgreen; ")
                    self.labelStatus.setText(txt)

                if event.type == JOYDEVICEREMOVED:

                    self.joysticks = self.add_remove_controllers()

                    txt = f"{self.deviceName} disonnected"

                    print(txt)
                    self.labelStatus.setStyleSheet("color: red; ")
                    self.labelStatus.setText(txt)

                pass

                # print(event)


            # sleep(6)

        print("Thread stopped")

        self.exitWindowAction()

    def closeEvent(self, event):
        
        # self.threadProcess.setDaemon
        # self.client.stop()
        # self.rabbitmq_flag.set()
        # self.mqtt_flag.set()
        try:
            
            self.stop_flag.set()
            event.accept()
            self.rabbitMQ_channel.stop_consuming()
            self.rabbitMQ_connection.close()

        except:

            print(" Cannot set Stop Flag ")

        windowHome.show()

        
        
        
    
    def exitWindowAction(self):

        self.close()
        windowHome.show()


    def startMultiprocess(self):

        self.timer_p2p= QTimer()
        self.timer_p2p.timeout.connect(self.TimerTriggerAction)
        self.timer_p2p.setInterval(500)
        self.timer_p2p.start()

    def TimerTriggerAction(self):

        pass
        

class AiWindow(base_22, form_22):

    def __init__(self, pipeline, motors):
        super(base_22, self).__init__()
        self.setupUi(self)
        self.pipeline   = pipeline
        self.motors     = motors
        self.ai     = AISettings()
        self.sys    = systemConfig
        self.ui     = systemUI
        self.resizeWindow()

        self.processTimer = Timer

        self.tsts = TimerCallbacks(var=self.pipeline)

        #Stop current preview
        self.pipeline.stop_preview()
        
        #Set button Actions
        self.closeButton.clicked.connect(self.closeEvent)
        self.buttonVericalCalibrtion.clicked.connect(self.buttonVericalCalibrtion_ClickAction)
        self.buttonVericalCalibrtion.clicked.connect(self.timer_tiltMotorCommandSend_function)
        self.buttonStartCorrection.clicked.connect(self.calibrationTimer_ClickAction)
        self.buttonGroup_Preview.buttonClicked.connect(self.buttonGroup_Preview_ClickAction)


        self.buttonIncrease3DLevel.clicked.connect(self.plus3DLevel)
        self.buttonDecrease3DLevel.clicked.connect(self.minus3DLevl)

        self.closeButton.setIconSize(ICON_SIZE)

        # Define variables
        self.previous_difference = 0
        self.previous_error = 0
        self.total_error = 0
        self.selectedTime = 10

        self.selected_preview = "preview2"


        

        self.set_point = int(self.ai.SET_POINT)

        val = self.set_point
        val = str(val)
        # self.labelSetPoint.setText(val)

        self.OpenPreviewAtStartup()
        self.buttonPreview_action()
        self.labelDetetctedMsg_timer()
        self.startHumanDetection()
        # self.buttonVericalCalibrtion_ClickAction()

        # self.buttonRigController.setVisible(False)
        width = int(self.ai.FRAME_WIDTH/2)
        height= (self.ai.FRAME_HEIGHT)

        self.black_frame = np.zeros((height, width, 3), dtype=np.uint8)

        self.buttonLable.setEnabled(False)


    def plus3DLevel(self):
        control_motor_L  = 3
        control_motor_R  = 4
        dir = self.ai.HCALIB_DIRECTION
        nu_of_steps = self.ai.CHANGE_3D_LEVEL
        cmd = self.motors.move_steps(m1=control_motor_L, m2=control_motor_R, move=True, direction=dir, steps=nu_of_steps)
        self.motors.sendSerialCommand(cmd=cmd)
        pass

    def minus3DLevl(self):
        control_motor_L  = 3
        control_motor_R  = 4
        dir = not self.ai.HCALIB_DIRECTION
        nu_of_steps = self.ai.CHANGE_3D_LEVEL
        cmd = self.motors.move_steps(m1=control_motor_L, m2=control_motor_R, move=True, direction=dir, steps=nu_of_steps)
        self.motors.sendSerialCommand(cmd=cmd)
        pass



    def buttonGroup_Preview_ClickAction(self, button):

        if button.objectName().__eq__("buttonSBSPreview"):
            self.selected_preview = "preview1"    # side by side preview

        if button.objectName().__eq__("buttonBlendPreview"):
            self.selected_preview = "preview2"     # blend preview

        if button.objectName().__eq__("buttonDetectionPreview"):
            self.selected_preview = "preview3"      # detection preview
            
        pass


    def label_update(self):
        # self.labelDetetctedMsg.setStyleSheet("")

        state = self.tsts.labelDetetcted_state
        text = "Object Detected"

        if state == False:

            self.labelDetetctedMsg.setStyleSheet("color: gray; ")
            text = "Object Not Detected"
            self.buttonLable.setEnabled(False)

        elif state == True:
            self.labelDetetctedMsg.setStyleSheet("color: lightgreen; ")
            self.buttonLable.setEnabled(True)

        else:
            text = ""

        self.labelDetetctedMsg.setText(text)


        # state = str(self.tsts.tilt_motor_state)
        # self.labelUpdateVerticalCalibration.setText(state)

        vdiff = str(self.tsts.vertical_difference)
        self.labelUpdateVerticalDiff.setText(vdiff)


    def labelDetetctedMsg_timer(self):

        self.timer_labelDetetctedMsg = QTimer()
        self.timer_labelDetetctedMsg.timeout.connect(self.label_update)
        self.timer_labelDetetctedMsg.setInterval(1000)
        self.timer_labelDetetctedMsg.start()


    def buttonVericalCalibrtion_ClickAction(self):

        self.timer_verticalCalibration = QTimer()
        self.timer_verticalCalibration.timeout.connect(self.verticalCalibration_TimerTriggerAction)
        self.timer_verticalCalibration.setInterval(500)
        self.timer_verticalCalibration.start()


    def verticalCalibration_TimerTriggerAction(self):

        self.tsts.verticalCalibration()


    def timer_tiltMotorCommandSend_function(self):
        
        
        self.timer_tiltMotorCommandSend=QTimer()
        self.timer_tiltMotorCommandSend.timeout.connect(self.tiltMotorCommandSend)
        self.timer_tiltMotorCommandSend.setInterval(500)
        self.timer_tiltMotorCommandSend.start()
        

    def tiltMotorCommandSend(self):


        d = self.tsts.vertical_difference

        if d<-70:

            state = "Difference Too high"
            self.labelUpdateVerticalCalibration.setText(state)
            self.buttonVericalCalibrtion.setChecked(False)
            self.buttonVericalCalibrtion.setEnabled(True)

        else:
            if -1<d and d <1 :
                
                self.timer_tiltMotorCommandSend.stop()
                self.buttonVericalCalibrtion.setChecked(False)
                self.timer_verticalCalibration.stop()
                state = "Vertical Calibration Done"
                self.labelUpdateVerticalCalibration.setText(state)

            else :
                self.tsts.caliculatePID()
            

    def OpenPreviewAtStartup(self): # delay 0.5 seconds . otherwise error occure
        def sss():
            self.buttonSBS_ClickedAction()
        t = self.processTimer(1 ,sss)
        t.start()

    def buttonPreview_action(self):
        self.time_viwer = QTimer()
        self.time_viwer.timeout.connect(self.preview)
        self.time_viwer.start(100)

    def buttonCheckerboard_ClickAction(self):
        self.timer_checherboard = QTimer()
        self.timer_checherboard.timeout.connect(self.start_ObjectDetection)
        self.timer_checherboard.start(1000) 

    def startHumanDetection(self):
        self.timer_humanDetection_process = QTimer()
        self.timer_humanDetection_process.timeout.connect(self.humanDetection)
        self.timer_humanDetection_process.start(2000)         

    def buttonStartCalibration_ClickedAction(self):
        self.timer_moveMotors = QTimer()
        self.timer_moveMotors.timeout.connect(self.start_MotorMovement)
        self.timer_moveMotors.start(2000)


    def preview(self):
        if self.pipeline.frame_update is not None:


            frame = self.pipeline.frame_update
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
            height, width = frame.shape[:2]

            # Step 3: Split the image into two parts vertically using NumPy slicing
            split_position = width // 2
            left_half   = frame[:, :split_position]
            right_half  = frame[:, split_position:]

            
            

            if self.selected_preview == "preview1":

                frame = cv2.hconcat([left_half, right_half])

            if self.selected_preview == "preview3":

                frame = self.tsts.sbs_frame_with_detection

            if self.selected_preview == "preview2":

                frame = cv2.absdiff(left_half, right_half)

                frame = cv2.hconcat([self.black_frame, frame, self.black_frame])



            h, w, ch = frame.shape
            q_img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)

            # Create a QPixmap and set it to the QLabel
            pixmap = QPixmap.fromImage(q_img)
            self.labelViewFrames.setPixmap(pixmap)
            self.labelViewFrames.show()



    def humanDetection(self):
        # self.tsts.buttonObjectDetection_ClickAction()

        self.tsts.newDetection()

        text = self.tsts.update_label_text
        self.labelDetetctedMsg.setText(text)

        texx = self.tsts.finalDifference
        texx = str(texx)
        self.labelUpdateDiff.setText(texx)


    def buttonSBS_ClickedAction(self):
        self.pipeline.pipeline_appsink()


    def getSelectedTime(self):

        index = self.comboBoxSelectTime.currentIndex()


        if index==0:
            t=0
        elif index==1:
            t=5
        elif index==2:
            t=10
        elif index==3:
            t=15
        elif index==4:
            t=20
        else:
            t=10


        self.selectedTime = t


    def calibrationTimer_ClickAction(self, button):

        self.buttonStartCorrection.setEnabled(False)

        self.getSelectedTime()
        self.time = self.selectedTime
        self.function()

    def function(self):

        self.timer_Calibration = QTimer()
        self.timer_Calibration.timeout.connect(self.timerFunction)
        self.timer_Calibration.start(1000)

    def timerFunction(self):

        t = str(self.time)
        text = f'Calibration Start In {t} seconds'
        self.time = self.time - 1

        if self.time > 0:
            self.labelUpdateState.setText(text)

        else :
            text = "Calibration started"
            self.labelUpdateState.setText(text)
            self.timer_Calibration.stop()
            self.buttonStartCalibration_ClickedAction()



    def start_MotorMovement(self):

        diff = self.tsts.finalDifference

        if diff is not None:

            if diff > (self.set_point+1) or diff < (self.set_point-1):

            
                if self.tsts.labelDetetcted_state == True :

                    self.tsts.sendMotorCommand(diff = diff)

                text = "Calibrating..."
                self.labelUpdateState.setText(text)

            else:

                self.buttonStartCorrection.setChecked(False)
                self.buttonStartCorrection.setEnabled(True)
                self.timer_moveMotors.stop()
                text = "ZeroPoint Calibration Done"
                self.labelUpdateState.setText(text)
                # self.timer_humanDetection_process.stop()
                self.tsts.labelDetetctedMsg_Text=""


    def closeEvent(self, event):

        if hasattr(self, 'timer_tiltMotorCommandSend'):
            self.timer_tiltMotorCommandSend.stop()
            del self.timer_tiltMotorCommandSend

        if hasattr(self, 'timer_moveMotors'):
            self.timer_moveMotors.stop()
            del self.timer_moveMotors

        if hasattr(self, 'timer_humanDetection_process'):
            self.timer_humanDetection_process.stop()
            del self.timer_humanDetection_process

        if hasattr(self, 'timer_verticalCalibration'):
            self.timer_verticalCalibration.stop()
            del self.timer_verticalCalibration

        if hasattr(self, 'time_viwer'):
            self.time_viwer.stop()
            del self.time_viwer

        self.pipeline.stop_preview()
        self.close()
        windowHome.show()
        


    def resizeWindow(self):

        self.x = self.ui.AI_WINDOW_SIZE_X
        self.y = self.ui.AI_WINDOW_SIZE_Y

        self.resize(int(self.x), int(self.y))

        self.mainPanelHeight = self.ui.MAIN_WINDOW_SIZE_Y

        self.Y = screen_height - 2*int(self.mainPanelHeight)
        self.Y = 100

        # self.move(int(self.x),int(self.Y))
        pass

    def resizeEvent(self, event):

        size = self.size()
        self.x = size.width()
        self.y = size.height()
        self.ui.AI_WINDOW_SIZE_X = self.x
        self.ui.AI_WINDOW_SIZE_Y = self.y
        self.ui.save()


class Select3DPreview(base_21, form_21):

    def __init__(self, pipeline):
        super(base_21, self).__init__()
        self.setupUi(self)
        self.pipeline = pipeline
        self.sys = systemConfig
        
        self.ui = systemUI
        self.resizeWindow()


        self.closeButton_previewWindow.clicked.connect(self.closeEvent)

        self.buttonRightPreview.clicked.connect(self.closeEvent)
        self.buttonLeftPreview.clicked.connect(self.closeEvent)
        self.pushButtonBlnd.clicked.connect(self.closeEvent)
        self.pushButtonSBS.clicked.connect(self.closeEvent)
        
        self.pushButtonBlnd.clicked.connect(self.startBlend)
        self.pushButtonSBS.clicked.connect(self.startSidebyside)
        self.buttonLeftPreview.clicked.connect(self.startLeftCam)
        self.buttonRightPreview.clicked.connect(self.startRightCam)

        # Set icon sizes

        self.closeButton_previewWindow.setIconSize(ICON_SIZE*0.8)


    def startLeftCam(self):

        self.pipeline.stop_preview()
        sleep(2)
        self.pipeline.leftCameraPreview()
        pass

    def startRightCam(self):

        self.pipeline.stop_preview()
        sleep(2)
        self.pipeline.rightCameraPreview()
        pass


    def startBlend(self):
        self.pipeline.stop_preview()
        sleep(2)
        self.pipeline.preview_3D(mode="blended", quality="720p")


    def startSidebyside(self):
        self.pipeline.stop_preview()
        sleep(2)
        # self.pipeline.preview_3D(mode="sbs", quality="720p")
        self.pipeline.sideBysidePreview()


    def closeEvent(self, event):

        self.close()

    def resizeWindow(self):

        self.x = self.ui.SELECT_3D_PREVIEW_WINDOW_X
        self.y = self.ui.SELECT_3D_PREVIEW_WINDOW_Y

        self.resize(int(self.x), int(self.y))

        self.mainPanelHeight = self.ui.MAIN_WINDOW_SIZE_Y

        self.Y = screen_height - 2*int(self.mainPanelHeight)
        self.Y = 100

        # self.move(int(self.x),int(self.Y))
        pass

    def resizeEvent(self, event):

        size = self.size()
        self.x = size.width()
        self.y = size.height()
        self.ui.SELECT_3D_PREVIEW_WINDOW_X = self.x
        self.ui.SELECT_3D_PREVIEW_WINDOW_Y = self.y
        self.ui.save()



class StreamWindow(base_4, form_4):


    def __init__(self,pipeline) :
        super(base_4,self).__init__()
        self.setupUi(self)

        self.pipeline = pipeline
        self.sys = systemConfig
        self.vid = systemCamera
        self.ui = systemUI

        # Initialise funtions
        self.resize_window()
        self.setIconSizes()
        self.setButtonFunctions()


        # check a user already login
        self.checkLoginState()
        self.applyLoadingGif()

        
        self.threadingTimer = Timer

        self.api_endpoint = f'{self.sys.APPLICATION_SERVER_URL}/user/signin'
        self.api_endpoint_for_ChannelInfor = f'{self.sys.APPLICATION_SERVER_URL}/channel/getchannelinfo'


        # Initial button layout

        self.labelShowStreamTimer.setVisible(False)
        self.buttonStopStream.setVisible(False)
        self.buttonStop4K.setVisible(False)

        if self.vid.ENABLE_4K_STREAM==False:
            self.buttonPlayStream4K.setVisible(False)

        self.labelLoadingIcon.setVisible(False)


    def checkLoginState(self):
        global LOGIN_STATE

        if LOGIN_STATE == 0:
            self.userNotLoggedIn()
        else:
            self.userLoggedIn()
            

    def userNotLoggedIn(self):
        self.buttonLogout.setVisible(False)
        

    def userLoggedIn(self):
        self.buttonLogin.setVisible(False)
        self.labelUsername.setVisible(False)
        self.lineEditUsername.setVisible(False)
        self.labelPassword.setVisible(False)
        self.lineEditPassword.setVisible(False)

        global DISPLAY_USERNAME
        global ADMIN_IMAGE

        if ADMIN_IMAGE is not None:
            
            self.labelProfileImage.setPixmap(ADMIN_IMAGE)
            pass

        # if DISPLAY_USERNAME is not None:

        self.labelFullName.setText(DISPLAY_USERNAME)
        self.labelFullName.setStyleSheet("color: rgb(255,255,255)")


    def setButtonFunctions(self):

        self.buttonPlayStream.clicked.connect(self.buttonPlayStreamClickAction)
        self.buttonStopStream.clicked.connect(self.buttonStopStreamClickAction)
        self.buttonLogin.clicked.connect(self.loginButtonPressAction)
        # self.buttonLogin.clicked.connect(self.loginButtonPressAction__)
        
        self.buttonExit.clicked.connect(self.closeEvent)
        self.buttonLogout.clicked.connect(self.logoutAction)
        self.buttonPlayStream4K.clicked.connect(self.buttonPlayStream4KAction)
        self.buttonStop4K.clicked.connect(self.buttonStop4KAction)
        self.buttonKeyboard.clicked.connect(self.keyBoardPopup)
        self.buttonSettingsStreamWindow.clicked.connect(self.buttonSettings_clickedAction)


    def buttonSettings_clickedAction(self):

        self.settingsWindow = Camera_Settings(cm)
        # self.settingsWindow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.settingsWindow.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.settingsWindow.setWindowFlags(self.settingsWindow.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.settingsWindow.setWindowTitle(' ')
        # self.hide()
        self.settingsWindow.show()

        pass

    def keyBoardPopup(self):

        os.system("onboard")


    def stopLocalStream(self):

        self.pipeline.stop_recording()



    def setIconSizes(self):
        #Set icon sizes
        self.buttonExit.setIconSize(ICON_SIZE*0.8)
        self.buttonSettingsStreamWindow.setIconSize(ICON_SIZE)



    def setFontSizes(self):

        # font = QFont()
        # font.setPointSize(80)  # Set the font size to 16
        # self.labelShowStreamTimer.setFont(font)

        size = self.ui.TIMER_SIZE
        self.labelShowStreamTimer.setStyleSheet("font:{0}px ; color: rgb(255,255,255)".format(int(size)))


    def loginButtonPressAction(self):

        self.buttonLogin.setEnabled(False)
        self.buttonLogin.setText("Loading.....")

        # self.threadTimerForLogin()
        self.adminLogin_thread()
        pass


    def adminLogin_thread(self):
        self.rabbit_thread_process = threading.Thread(target=self.loginButtonPressAction__trig)
        # self.rabbit_thread_process.setDaemon
        self.rabbit_thread_process.start()

    # def threadTimerForLogin(self):

    #     def triggerFunction():
    #         self.loginButtonPressAction__trig()

    #     t=self.threadingTimer(2, triggerFunction)
    #     t.start()

        #     def sss():
        #     self.previewStart()
        # t = self.processTimer(1 ,sss)
        # t.start()


    def loginButtonPressAction__trig(self):


        self.buttonLogin.setEnabled(False)
        # self.buttonLogin.setStyleSheet("background-color: red;")

        self.labelFullName.setText("")

        self.username = self.lineEditUsername.text()
        self.password = self.lineEditPassword.text()
        
        data = {
            "Email": self.username,
            "Password": self.password
                }

        self.response = requests.post(self.api_endpoint, json=data, headers={'Content-Type': 'application/json'})

        # Check response is valid

        if self.response.status_code == 200:

            signin_data = self.response.json()

            rez = signin_data['result']
            accessToken = rez['accessToken']


            access_token = accessToken

            headers = {'Authorization': 'Bearer ' + access_token}
            
            # Send the HTTP request with the headers
            self.response_channelInfo = requests.get(self.api_endpoint_for_ChannelInfor, headers=headers)

            channelInfo_data = self.response_channelInfo.json()

            result_channelInf = channelInfo_data['result']

            self.admin_image_url = result_channelInf['channelThumbnailUrl']
            keystream = result_channelInf['streamKey3D']


            global STREAM_KEY

            STREAM_KEY = keystream.strip()

            firstName = rez['firstName']
            secondName = rez['lastName']
            fullName =   firstName + ' ' + secondName
            self.labelFullName.setText(fullName)
            self.labelFullName.setStyleSheet("color: rgb(255,255,255)")

            self.loggedInButtonLayout()

            global LOGIN_STATE

            LOGIN_STATE = 1

            global DISPLAY_USERNAME
            
            DISPLAY_USERNAME = str(fullName)

            try :
                self.applyImageToLabel()
            except:
                print("Unable to apply image")


        else:
 
            self.buttonLogin.setText("Login")
            # Enable Login Button
            self.buttonLogin.setEnabled(True)
            # self.labelLoadingIcon.setVisible(False)
            self.buttonLogin.setStyleSheet("background-color: blue;")
            
            text = 'Invalid Username or Password'
            self.labelFullName.setText(text)
            # self.lineEditUserName.setStyleSheet("color: red;")

            
    def applyLoadingGif(self):

        gif_path = "resize.gif"
        movie = QMovie(gif_path)
        self.labelLoadingIcon.setMovie(movie)
        # Start the animation
        movie.start()

        pass


    def download_image(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
            else:
                print("Failed to download image. Status code:", response.status_code)
                return None
        except Exception as e:
            print("Error:", e)
            return None


    def applyImageToLabel(self):

        image_data = self.download_image(url=self.admin_image_url)

        image_size = self.ui.ADMIN_IMAGE_SIZE

        admin_image_w,admin_image_h = image_size.split(',')


        global ADMIN_IMAGE

        if image_data:
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            pixmap = pixmap.scaled(int(admin_image_w), int(admin_image_h))
            ADMIN_IMAGE = pixmap
            if ADMIN_IMAGE is not None:

                self.labelProfileImage.setPixmap(ADMIN_IMAGE)
        else:
            print("Image Data Invalid")


    def loggedInButtonLayout(self):

        try :

            self.buttonLogout.setVisible(True)
            self.labelUsername.setVisible(False)
            self.lineEditUsername.setVisible(False)
            self.labelPassword.setVisible(False)
            self.lineEditPassword.setVisible(False)
            self.buttonLogin.setVisible(False)

        except:

            print("Unable to Detect buttons. Plese check the ui")


    def logoutAction(self):

        # self.buttonLogin.setEnabled(True)

        self.buttonLogin.setText("Login")

        self.buttonLogout.setVisible(False)
        self.labelUsername.setVisible(True)
        self.lineEditUsername.setVisible(True)
        self.labelPassword.setVisible(True)
        self.lineEditPassword.setVisible(True)
        self.buttonLogin.setVisible(True)


        global STREAM_KEY
        global ADMIN_IMAGE

        ADMIN_IMAGE = None


        STREAM_KEY = None
        text=" "
        self.lineEditUsername.setText(text)
        self.lineEditPassword.setText(text)
        self.labelFullName.setText(text)

        global LOGIN_STATE

        LOGIN_STATE = 0

        # Clear Admin Image

        self.labelProfileImage.clear()


    def minimize_window(self):
        # Resize the window
        

        # x=self.sys.STREAM_WINDOW_MIN_X
        # y=self.sys.STREAM_WINDOW_MIN_Y
        x=screen_width/6
        y=screen_height/4
        self.resize(int(x),int(y))
        self.move(0, 0)
        # self.buttonExit.setVisible(False)
        self.buttonPlayStream.setVisible(False)
        self.buttonStopStream.setVisible(True)

        self.buttonLogout.setVisible(False)
        self.labelShowStreamTimer.setVisible(True)


    def resize_window(self):

        
        
        # self.move((screen_width/2 - scaled_width_3/2), (screen_height/2- scaled_height_4/2))
        self.move(int(screen_width/3) , int(screen_height/3))
        # self.buttonExit.setVisible(True)
        self.buttonStopStream.setVisible(False)
        self.buttonPlayStream.setVisible(True)


        self.labelShowStreamTimer.setVisible(False)

        x=self.ui.STREAM_WINDOW_SIZE_X
        y=self.ui.STREAM_WINDOW_SIZE_Y


        self.resize(x,y)


    def resizeEvent(self, event):
 
        size = self.size()
        self.widthStream = size.width()
        self.heightStream = size.height()
    

    def savewindowSize(self):


        self.ui.STREAM_WINDOW_SIZE_X = self.widthStream
        self.ui.STREAM_WINDOW_SIZE_Y = self.heightStream

        self.ui.save()


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Store the initial mouse position and window position
            self.startPos = event.globalPos()
            self.windowPos = self.frameGeometry().topLeft()


    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # Calculate the new window position based on the mouse movement
            delta = event.globalPos() - self.startPos
            self.move(self.windowPos + delta)


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Clear the stored positions
            self.startPos = None
            self.windowPos = None


    def streamPlayAction(self):
        self.setFontSizes()
        self.minimize_window()
        self.buttonPlayStream.setEnabled(False)
        self.buttonStopStream.setEnabled(True)
        self.buttonExit.setVisible(False)
        self.buttonPlayStream4K.setVisible(False)
        self.buttonKeyboard.setVisible(False)

        self.timer=QTimer(self)
        self.timer.timeout.connect(self.showStreamTime)
        self.timeStarted = 0
        self.state = True

        self.startStreamTimer()
        
        self.pipeline.stop_preview()
        time.sleep(3)


    def buttonPlayStream4KAction(self):

        self.buttonPlayStream.setVisible(False)
        self.buttonStop4K.setVisible(True)
        self.buttonPlayStream4K.setVisible(False)
        self.buttonExit.setVisible(False)

        self.buttonLogout.setVisible(False)
        self.labelUsername.setVisible(False)
        self.lineEditUsername.setVisible(False)
        self.labelPassword.setVisible(False)
        self.lineEditPassword.setVisible(False)
        self.buttonLogin.setVisible(False)
        

        self.pipeline.stream_rtmp_4k()


    def buttonStop4KAction(self):

        self.buttonStop4K.setVisible(False)
        self.buttonPlayStream.setVisible(True)
        self.buttonPlayStream4K.setVisible(True)
        self.buttonExit.setVisible(True)

        # self.buttonLogout.setVisible(False)
        self.labelUsername.setVisible(True)
        self.lineEditUsername.setVisible(True)
        self.labelPassword.setVisible(True)
        self.lineEditPassword.setVisible(True)
        self.buttonLogin.setVisible(True)

        self.pipeline.stop_recording()


    def buttonPlayStreamClickAction(self):



        # pree = self.theMain.desable()

        global MAIN_WINDOW_CLICKABLE 
        MAIN_WINDOW_CLICKABLE = False

        global STREAM_KEY

        if STREAM_KEY is not None:
            self.streamPlayAction()

            # self.pipeline.stream_rtmp(stream_key=STREAM_KEY)
            self.pipeline.stream_rtmp_4k()


        if STREAM_KEY is None:
            
            self.labelFullName.setText("Please login to Start Stream")
            # text_color = QColor('red')
            # self.lineEditUserName.setTextColor(text_color)

            self.labelFullName.setStyleSheet("color: rgb(235,52,52)")

            # if self.checkBoxStream4K.isChecked():
            #     self.checkBoxStream4K.setVisible(False)
            #     self.pipeline.stream_rtmp_4k()


    def closeEvent(self, event):
        self.savewindowSize()
        self.close()
        windowHome.show()
            

    def buttonStopStreamClickAction(self):


        global MAIN_WINDOW_CLICKABLE 
        MAIN_WINDOW_CLICKABLE = True

        self.resize_window()
        
        # self.saveSize()
        self.buttonPlayStream.setEnabled(True)
        self.buttonStopStream.setEnabled(False)
        self.buttonExit.setVisible(True)
        self.buttonLogout.setVisible(True)
        # self.buttonPlayStream4K.setVisible(True)
        self.buttonKeyboard.setVisible(True)

        if self.vid.ENABLE_4K_STREAM:
            self.buttonPlayStream4K.setVisible(True)
            
        

        self.endStreamTimer()

        self.savewindowSize()

        # self.pipeline.stop()

        self.pipeline.stop_recording()


    def startStreamTimer(self):
        self.labelShowStreamTimer.setText("00:00:00")
        self.timer.start(1000)
        self.timeStarted = QDateTime.currentSecsSinceEpoch()


    def endStreamTimer(self):
        self.timer.stop()
        self.timeStarted = 0

        # capture duration timer reset
        self.captureDuration = 0


    def showStreamTime(self):
        __now = QDateTime.currentSecsSinceEpoch()


        if self.timeStarted != 0:
            total_seconds = __now - self.timeStarted

            hours           = total_seconds // 3600
            total_seconds   = total_seconds - (hours * 3600)
            minutes         = total_seconds // 60
            seconds         = total_seconds - (minutes * 60)

            
            self.labelShowStreamTimer.setText("{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds)))


class VideoEditorWindow(base_25, form_25):

    def __init__(self, pipeline):
        super(base_25, self).__init__()
        self.setupUi(self)
        self.pipeline=pipeline
        self.vid = systemCamera

        self.buttonStartPostprocess.clicked.connect(self.buttonStartPostprocess_ClickAction)
        self.buttonStopPostProcess.clicked.connect(self.buttonStopPostProcess_ClickAction)
        self.buttonExit.clicked.connect(self.closeEvent)
        self.buttonExit.setIconSize(ICON_SIZE)


        self.loadFilesForPostprocess()

        # self.comboBoxSelectPPVideo.activated.connect(self.comboBoxClickAction)

    def comboBoxClickAction(self):

        content = self.comboBoxSelectPPVideo.currentText()
        # self.textEditDisplayVideoName.setText(content)



    def loadFilesForPostprocess(self):

        self.lastvideopath = self.vid.DROP_LOCATION
            
        list_of_files = glob.glob('{0}*'.format(self.lastvideopath)) 

        video_files = [f for f in list_of_files if os.path.splitext(f)[1] in['.mkv', '.mp4'] and not os.path.basename(f).startswith('SH_')]

        video_files = sorted(video_files, key=os.path.getctime, reverse=True)

        self.video_list = []

        for x in range(len(video_files)):
            # print(list_of_files[x], sep = "\n")
            latest_file = video_files[x].replace('{0}'.format(self.lastvideopath), '')
            self.video_list.append(latest_file)

        # self.video_list.sort(key=lambda x: x[1], reverse=True)

        for y in range (len(self.video_list)):

            self.comboBoxSelectPPVideo.addItem(self.video_list[y])
        


    def buttonStartPostprocess_ClickAction(self):

        self.buttonStartPostprocess.setEnabled(False)
        self.buttonExit.setVisible(False)

        filename = self.comboBoxSelectPPVideo.currentText()

        print(filename)
        self.pipeline.post_process(source_file=filename)

        pass

    def buttonStopPostProcess_ClickAction(self):

        self.buttonStartPostprocess.setEnabled(True)
        self.buttonExit.setVisible(True)

        self.pipeline.stop_preview()

        print("Post process ended")

        pass

    def closeEvent(self, event):

        self.close()
        windowHome.show()

        pass


class MediaWindow(base_24, form_24):

    def __init__(self, pipeline):
        super(base_24, self).__init__()
        self.setupUi(self)
        self.pipeline=pipeline
        self.sys = systemConfig
        self.ui = systemUI

        self.buttonVideoPlayer.clicked.connect(self.buttonVideoPlayer_ClickAction)
        self.buttonVideoPlayer.setIconSize(ICON_SIZE)
        self.buttonPostProcess.clicked.connect(self.buttonPostProcess_ClickAction)
        self.buttonPostProcess.setIconSize(ICON_SIZE)
        self.buttonExit.clicked.connect(self.closeEvent)
        self.buttonExit.setIconSize(ICON_SIZE)

        self.resize_window()


    def resize_window(self):

        size = self.ui.MEDIA_WINDOW_SIZE
        w,h = size.split(',')
        self.resize(int(w),int(h))

    def resizeEvent(self, event):

        size = self.size()
        x = size.width()
        y = size.height()
        new_size = str(x)+","+str(y)
        self.ui.MEDIA_WINDOW_SIZE = new_size
        self.ui.save()

    def closeEvent(self, event):
        self.close()
        windowHome.show()
        pass

    def buttonVideoPlayer_ClickAction(self):

        self.videoPlayer_Window = VideoPlayerWindow(cm)
        self.videoPlayer_Window.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.videoPlayer_Window.setWindowFlags(self.videoPlayer_Window.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.videoPlayer_Window.setWindowTitle(' Media ')
        self.hide()
        self.videoPlayer_Window.show()
        pass

    def buttonPostProcess_ClickAction(self):

        self.postProcess_Window = VideoEditorWindow(cm)
        self.postProcess_Window.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.postProcess_Window.setWindowFlags(self.postProcess_Window.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.postProcess_Window.setWindowTitle(' Video Editor ')
        self.hide()
        self.postProcess_Window.show()
        pass



class VideoPlayerWindow(base_19, form_19):

    def __init__(self, pipeline):
        super(base_19,self).__init__()
        self.setupUi(self)      
        self.sys = systemConfig
        self.ui = systemUI
        self.pipeline = pipeline

        self.setWindowSize()

        self.vid=systemCamera

        self.buttonPlayVideo.clicked.connect(self.buttonPlayVideoClickAction)
        # self.buttonPostProcess.clicked.connect(self.buttonPostProcessClickAction)
        self.buttonExit.clicked.connect(self.closeEvent)
        self.buttonStopRecord.clicked.connect(self.stopVideo)
        self.pushButtonPaused.clicked.connect(self.pauseButtonAction)
        # self.buttonCaptureImage.clicked.connect(self.captureImage)

        self.updateRecordFileName()
        
        self.loadFilesInDropLocation()

        self.comboBoxSelectVideo.activated.connect(self.do_something)
        
        self.buttonExit.setIconSize(ICON_SIZE*0.8)
        self.buttonStopRecord.setIconSize(ICON_SIZE*1.2)
        self.buttonPlayVideo.setIconSize(ICON_SIZE)
        self.windowIconRec.setIconSize(ICON_SIZE)
        self.pushButtonPaused.setIconSize(ICON_SIZE)


        # self.buttonCaptureImage.setVisible(False)


    def captureImage(self):


        self.pipeline.saveImage()


    def setWindowSize(self):
        self.x=self.ui.GALLERY_WINDOW_SIZE_X
        self.y=self.ui.GALLERY_WINDOW_SIZE_Y
        
        self.resize(self.x ,self.y)


    def resizeEvent(self, event):
        
        size = self.size()
        self.x = size.width()
        self.y = size.height()
  

    def saveSize(self):


        
        self.ui.GALLERY_WINDOW_SIZE_X = self.x
        self.ui.GALLERY_WINDOW_SIZE_Y = self.y
        self.ui.save()


    def pauseButtonAction(self):

        global PLAYING_STATE

        PLAYING_STATE = not PLAYING_STATE

        if PLAYING_STATE is True:

            self.pipeline.pause_pipeline()

        if PLAYING_STATE is False:

            self.pipeline.ready_pipeline()


    def stopVideo(self):

        self.pipeline.stop_recording()


    def do_something(self):
        content = self.comboBoxSelectVideo.currentText()
        self.textEditDisplayVideoName.setText(content)

    
    def buttonPostProcessClickAction(self):
        filename = self.textEditDisplayVideoName.text()
        self.pipeline.post_process(source_file=filename)

    
    def buttonPlayVideoClickAction(self):
        
        filename = self.textEditDisplayVideoName.text()
        self.pipeline.video_player(source_file=filename)


    def updateRecordFileName(self):

        try:
            
            self.lastvideopath = self.vid.DROP_LOCATION
            list_of_files = glob.glob('{0}*'.format(self.lastvideopath)) 
            # list_of_files = glob.glob(self.lastvideopath)
            mp4_files = [f for f in list_of_files if os.path.splitext(f)[1] in['.mkv', '.mp4'] ]
            self.latest_file__ = max(mp4_files, key=os.path.getctime)
            self.latest_file = self.latest_file__.replace('{0}'.format(self.lastvideopath), '')
            self.textEditDisplayVideoName.setText(self.latest_file)

          
        except:
            self.textEditDisplayVideoName.setText("No Recorded videos")      


    def loadFilesInDropLocation(self):

        self.lastvideopath = self.vid.DROP_LOCATION
            
        list_of_files = glob.glob('{0}*'.format(self.lastvideopath)) 

        mp4_files = [f for f in list_of_files if os.path.splitext(f)[1] in['.mkv', '.mp4']]

        mp4_files = sorted(mp4_files, key=os.path.getctime, reverse=True)

        self.video_list = []

        for x in range(len(mp4_files)):
            # print(list_of_files[x], sep = "\n")
            latest_file = mp4_files[x].replace('{0}'.format(self.lastvideopath), '')
            self.video_list.append(latest_file)

        # self.video_list.sort(key=lambda x: x[1], reverse=True)

        for y in range (len(self.video_list)):

            self.comboBoxSelectVideo.addItem(self.video_list[y])
        

    def closeEvent(self, event):

        # if hasattr(self, 'timer_tiltMotorCommandSend'):
        #     self.timer_tiltMotorCommandSend.stop()
        #     del self.timer_tiltMotorCommandSend
        if hasattr(self.pipeline, 'pipeline') and self.pipeline.pipeline is not None:
            self.pipeline.stop_recording()

        self.saveSize()
        self.close()
        windowHome.show()

        pass


class recordWindow(base_3, form_3):

    def __init__(self, pipeline):
        super(base_3, self).__init__()
        self.setupUi(self)
        self.pipeline=pipeline
        self.sys = systemConfig
        self.vid = systemCamera
        self.ui = systemUI
        self.initFunction()

        self.screen_width = screen_width
        self.screen_height = screen_height


        self.buttonStopRecord.setVisible(False)
        self.buttonStartRecord.setVisible(True)
        self.labelRecordTimer.setVisible(False)
        self.pushButtonPaused.setVisible(False)

        self.processTimer = Timer

        self.updateAvailableStorage_startUp()

        


    def initFunction(self):
        # self.updateRecordFileName()
        self.setFontSizes()
        self.setIconSize()
        self.setButtonActions()
        self.setWindowSize()


    def setButtonActions(self):
        self.buttonStartRecord.clicked.connect(self.buttonRecordStartClickAction)
        self.buttonStopRecord.clicked.connect(self.buttonRecordStopClickAction)
        self.buttonExit.clicked.connect(self.closeEvent)
        self.pushButtonPaused.clicked.connect(self.pauseButtonAction)
        self.buttonOpenCameraSettings.clicked.connect(self.buttonOpenCameraSettings_clickAction)


    def buttonOpenCameraSettings_clickAction(self):
        
        self.settingsWindow = Camera_Settings(cm)
        # self.settingsWindow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.settingsWindow.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.settingsWindow.setWindowFlags(self.settingsWindow.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.settingsWindow.setWindowTitle(' ')
        # self.hide()
        self.settingsWindow.show()


    def timerUpdateStorage(self):
        self.timer_updateStorage = QTimer()
        self.timer_updateStorage.timeout.connect(self.updateAvailableStorage)
        self.timer_updateStorage.setInterval(30000)
        self.timer_updateStorage.start()

        
    def get_available_storage(self,path):
        try:
            df_output = subprocess.check_output(["df", "-h", path]).decode("utf-8")
            lines = df_output.split("\n")

            for line in lines[1:]:
                columns = line.split()
                if len(columns) >= 6 and columns[5] == path:
                    available_storage = columns[3]
                    return available_storage
        except subprocess.CalledProcessError:
            return None
        

    def updateAvailableStorage_startUp(self):

        try:

            nvme_path = self.sys.NVME_MOUNT_POINT

            if nvme_path.endswith('/'):
                nvme_path = nvme_path[:-1]

            available_storage = self.get_available_storage(nvme_path)

            
            if available_storage is not None:

                txt = f"Available storage : {available_storage}B"
            else:
                txt = "Error retrieving available storage information."

        


            if 'M' in available_storage :

                txt = "Unable to start Recording Due to Low storage"
                self.labelDisplayStorage.setStyleSheet("color: red; ")
                self.buttonStartRecord.setEnabled(False)
                pass

            elif 'G' in available_storage:


                # available storage out  as 1.5G  remove 'G'  and convert to float
                available_storage = float(available_storage.replace("G", ""))

                if available_storage < 2.0 :
                    # txt = f"Available storage : {available_storage}GB
                    txt = f"Storage is low. available storage {available_storage} "
                    self.labelDisplayStorage.setStyleSheet("color: red; ")

                if available_storage < 1.5 :
                    txt = "Unable to start Recording Due to Low storage"
                    self.labelDisplayStorage.setStyleSheet("color: red; ")
                    self.buttonStartRecord.setEnabled(False)

        except:
            txt = "Plese set NVME_PATH In system.yaml to get Storage Information"
            
        
        self.labelDisplayStorage.setText(txt)

    def updateAvailableStorage(self):

        # nvme_path = "/media/nvidia/GIOVIEW1/"

        try:

            nvme_path = self.sys.NVME_PATH

            if nvme_path.endswith('/'):
                nvme_path = nvme_path[:-1]

            
            available_storage = self.get_available_storage(nvme_path)


            if available_storage is not None:


                txt = f"Available storage : {available_storage}B"
            else:
                txt = "Error retrieving available storage information."


            # available storage out  as 1.5G  remove 'G'  and convert to float
            available_storage = float(available_storage.replace("G", ""))

            if available_storage < 2.0 :
                # txt = f"Available storage : {available_storage}GB
                txt = f"Storage is low. Recording Will end soon. available storage {available_storage}"

            if available_storage < 1.5 :
                txt = "Recording Ended due to Low storage"
                self.buttonStopRecord.click()
                print("Recording Ended")

        except:
            txt  = " "      
            pass

        self.labelDisplayStorage.setText(txt)

    def pauseButtonAction(self):

        global PLAYING_STATE

        PLAYING_STATE = not PLAYING_STATE

        if PLAYING_STATE is True:
            self.pipeline.pause_pipeline()

        if PLAYING_STATE is False:
            self.pipeline.ready_pipeline()

            
    def buttonRecordStartClickAction(self):
 

        self.startTimer()

        self.updateRecordFileName()

        self.buttonStartRecord.setVisible(False)
        self.buttonExit.setVisible(False)
        self.buttonStopRecord.setVisible(True)
        self.labelRecordTimer.setVisible(True)

        self.comboBoxFormat.setEnabled(False)
        self.comboBoxQuality.setEnabled(False)
        self.comboBoxFileFormat.setEnabled(False)

        # Clear last file name
        self.textEditDisplayVideoName.setText("")
        # Update Current File name
        self.UpdateLastFileName()
        self.timerUpdateStorage()


        if self.pipeline is not None: 
            self.pipeline.stop_preview()
            time.sleep(5)


        index = self.comboBoxQuality.currentIndex()


        fileformat_index = self.comboBoxFileFormat.currentIndex()

        if fileformat_index == 0:
            fileformat = "mp4"

        if fileformat_index == 1:
            fileformat = "mkv"

        if fileformat_index == 2:
            fileformat = "avi"

        # check 
        format = self.comboBoxFormat.currentIndex()

        if format==0:
            self.pipeline.record_h265(quality=("2160p" if index==0 else ("1080p" if index==1 else "720p")), file_type=fileformat)

        if format==1:
            self.pipeline.record_h264(quality=("2160p" if index==0 else ("1080p" if index==1 else "720p")), file_type=fileformat)


    def buttonRecordStopClickAction(self):

        # Stop timer
        self.timer.stop()
        self.timer_updateStorage.stop()
        self.timeStarted = 0

        # Change button states
        self.buttonStopRecord.setVisible(False)
        self.buttonStartRecord.setVisible(True)

        self.buttonExit.setVisible(True)
        self.labelRecordTimer.setVisible(False)

        self.comboBoxFormat.setEnabled(True)
        self.comboBoxQuality.setEnabled(True)
        self.comboBoxFileFormat.setEnabled(True)
        
        self.updateAvailableStorage_startUp()

        # Stop Pipeline
        self.pipeline.stop_recording()



    def startTimer(self):

        self.labelRecordTimer.setText("00:00:00")
        self.timeStarted = 0

        self.timer=QTimer(self)
        self.timer.timeout.connect(self.showTime)
        self.timer.start(1000)
        self.timeStarted = QDateTime.currentSecsSinceEpoch()


    def showTime(self):
        __now = QDateTime.currentSecsSinceEpoch()

        # show rec bin time
        if self.timeStarted != 0:
            total_seconds = __now - (self.timeStarted + 5)

            hours           = total_seconds // 3600
            total_seconds   = total_seconds - (hours * 3600)
            minutes         = total_seconds // 60
            seconds         = total_seconds - (minutes * 60)

            # print(total_seconds)

            if hours<0:
                self.labelRecordTimer.setText("--:--:--")
            else :
                self.labelRecordTimer.setText("{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds)))

        # set latest file name to the video player
    


    def UpdateLastFileName(self): # delay 0.5 seconds . otherwise error occure
        def sss():
            self.updateRecordFileName()
        t = self.processTimer(10 ,sss)
        t.start()

    
    def updateRecordFileName(self):

        try:
            
            self.lastvideopath = self.vid.DROP_LOCATION
            list_of_files = glob.glob('{0}*'.format(self.lastvideopath)) 
            # list_of_files = glob.glob(self.lastvideopath)
            mp4_files = [f for f in list_of_files if os.path.splitext(f)[1] in ['.mp4', '.mkv', '.avi']]
            self.latest_file__ = max(mp4_files, key=os.path.getctime)
            self.latest_file = self.latest_file__.replace('{0}'.format(self.lastvideopath), '')
            self.textEditDisplayVideoName.setText(self.latest_file)

          
        except:
            self.textEditDisplayVideoName.setText("No Recorded Videos")      





    def setWindowSize(self):
        self.x=self.ui.RECORD_WINDOW_SIZE_X
        self.y=self.ui.RECORD_WINDOW_SIZE_Y
        self.resize(self.x ,self.y)


    def resizeEvent(self, event):
        
        size = self.size()
        self.x = size.width()
        self.y = size.height()
  

    def saveSize(self):
        self.ui.RECORD_WINDOW_SIZE_X = self.x
        self.ui.RECORD_WINDOW_SIZE_Y = self.y
        self.ui.save()


    def setIconSize(self):

        try:
            self.buttonExit.setIconSize(ICON_SIZE*0.8)
            self.buttonStopRecord.setIconSize(ICON_SIZE*1.2)
            self.buttonStartRecord.setIconSize(ICON_SIZE)
            # self.buttonPlayVideo.setIconSize(ICON_SIZE)
            # self.windowIconRec.setIconSize(ICON_SIZE)
            self.buttonOpenCameraSettings.setIconSize(ICON_SIZE)

        except:
            print("***********Some buttons may missed")



    def setFontSizes(self):
        size = self.ui.TIMER_SIZE
        self.labelRecordTimer.setStyleSheet("font:{0}px ; color: rgb(255,255,255)".format(int(size)))


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startPos = event.globalPos()
            self.windowPos = self.frameGeometry().topLeft()


    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.startPos
            self.move(self.windowPos + delta)


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startPos = None
            self.windowPos = None


    def closeEvent(self, event):
        self.saveSize()
        self.close()
        windowHome.show()


class SettingsPage(base_9, form_9):
    def __init__(self):
        super(base_9, self).__init__()
        self.setupUi(self)
  
        # self.setGeometry(500, 150, 300, 300)
        self.sys = systemConfig
        self.ui = systemUI

        self.window_x = self.ui.SETTINGS_WINDOW_SIZE_X
        self.window_y = self.ui.SETTINGS_WINDOW_SIZE_Y

        self.resize(self.window_x, self.window_y)


        # self.setWindowTitle(" Settings ")
        self.buttonServoControls.clicked.connect(self.opneServoControlWindow)
        self.buttonStreamKey.clicked.connect(self.opneStreamKeyWindow)
        self.buttonFolder.clicked.connect(self.openRecordingPathWindow)
        self.buttonSettings.clicked.connect(self.OpenCamSettingsWindow)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.buttonExit.clicked.connect(self.closeEvent)
        self.buttonPresets.clicked.connect(self.openPresetsWindow)
        self.buttonDeviceSettings.clicked.connect(self.openDevSettingsWindow)

        # self.buttonServoControls.setIconSize(ICON_SIZE*1.5)
        # self.buttonStreamKey.setIconSize(ICON_SIZE*1.5)
        # self.buttonFolder.setIconSize(ICON_SIZE*1.5)
        # self.buttonSettings.setIconSize(ICON_SIZE*1.5)
        # self.buttonExit.setIconSize(ICON_SIZE*0.8)
        # self.buttonPresets.setIconSize(ICON_SIZE*0.8)

        self.buttonServoControls.setIconSize(ICON_SIZE)
        self.buttonStreamKey.setIconSize(ICON_SIZE)
        self.buttonFolder.setIconSize(ICON_SIZE)
        self.buttonSettings.setIconSize(ICON_SIZE)
        self.buttonExit.setIconSize(ICON_SIZE*0.8)
        self.buttonPresets.setIconSize(ICON_SIZE)
        self.buttonDeviceSettings.setIconSize(ICON_SIZE)


    def openPresetsWindow(self):
        print
        self.windowPreset = Preset(mp)
        
        self.windowPreset.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.windowPreset.setWindowFlags(self.windowPreset.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.windowPreset.setWindowTitle(' ')
        self.close()
        self.windowPreset.show()


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Store the initial mouse position and window position
            self.startPos = event.globalPos()
            self.windowPos = self.frameGeometry().topLeft()


    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # Calculate the new window position based on the mouse movement
            delta = event.globalPos() - self.startPos
            self.move(self.windowPos + delta)


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Clear the stored positions
            self.startPos = None
            self.windowPos = None


    def resizeEvent(self, event):
        window = self.size()
        self.window_x = window.width()
        self.window_y = window.height()
        self.saveSettingWindowSize()


    def saveSettingWindowSize(self):

        self.ui.SETTINGS_WINDOW_SIZE_X = self.window_x
        self.ui.SETTINGS_WINDOW_SIZE_Y = self.window_y
        self.ui.save()

        pass
    
    
    def closeEvent(self, event):
        self.close()
        windowHome.show()


    def OpenCamSettingsWindow(self):
        self.windowServer = Camera_Settings(cm)
        self.windowServer.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.windowServer.setWindowFlags(self.windowServer.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.windowServer.setWindowTitle(' ')
        self.close()
        self.windowServer.show()


    def opneServoControlWindow(self):

        self.windowServer = RigControlPage(mp,cm)
        self.windowServer.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.windowServer.setWindowFlags(self.windowServer.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.windowServer.setWindowTitle(' ')
        self.close()
        self.windowServer.show()
        

    def opneStreamKeyWindow(self):

        self.windowServer = StreamKeyWindow()
        self.windowServer.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.close()
        self.windowServer.show()


    def openRecordingPathWindow(self):

        self.windowServer = FileManagerWindow()
        self.windowServer.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.close()
        self.windowServer.resize(int(screen_width/3),int(screen_height/4))
        self.windowServer.show()



    def openDevSettingsWindow(self):

        self.windowDeviceSettings = DeviceSettingsPage()
        self.windowDeviceSettings.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.windowDeviceSettings.setWindowFlags(self.windowDeviceSettings.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.windowDeviceSettings.setWindowTitle(' Device Settings ')
        self.close()
        self.windowDeviceSettings.show()



class DeviceSettingsPage(base_27, form_27):

    def __init__(self):
        super(base_27, self).__init__()
        # Initialize ui and yaml files----------------------
        self.setupUi(self)
        self.sys = systemConfig
        # self.vid = systemCamera
        self.ui = systemUI
        #---------------------------------------------------

        # Define Button actions--------
        self.pushButtonExitDeviceSettings.clicked.connect(self.exitAction)
        self.radioButtonSnapOn.clicked.connect(self.radioButtonClickedOn)
        self.radioButtonSnapOff.clicked.connect(self.radioButtonClickedOff)
        # ------------------------------

        # Enter calling functions here
        self.resizeWindow()
        self.listAudioDevice()
        self.checkSnapStartState()

    def radioButtonClickedOn(self):

        self.sys.SNAPSTART = True
        self.sys.save()

    def radioButtonClickedOff(self):

        self.sys.SNAPSTART = False
        self.sys.save()

    def checkSnapStartState(self):

        if self.sys.SNAPSTART==True:
            self.radioButtonSnapOn.setChecked(True)


    def exitAction(self):
        self.close()
        pass

    def resizeWindow(self):

        size = self.ui.DEVICE_SETTINGS_WINDOW_SIZE
        w,h = size.split(',')
        self.resize(int(w),int(h))

    def resizeEvent(self, event):

        size = self.size()
        x = size.width()
        y = size.height()
        new_size = str(x)+","+str(y)
        self.ui.DEVICE_SETTINGS_WINDOW_SIZE = new_size
        self.ui.save()
        print(new_size)

        pass

    def listAudioDevice(self):

        try:
            output = subprocess.check_output(['arecord', '-l'], stderr=subprocess.STDOUT, universal_newlines=True)
            lines = output.split('\n')
            
            usb_device_count = 0
            self.usb_device_list = []
            
            for line in lines:
                if "USB Audio Device" in line:
                    usb_device_count += 1
                    device_name = line.strip().split(":")[-1].strip()
                    self.usb_device_list.append(device_name)
            
            print(f"Total USB audio input devices detected: {usb_device_count}")
            print("List of available USB audio input device names:")
            # print("hhhh  ",self.usb_device_names)
            # print(", ".join(self.usb_device_names))  # Join the names with commas and print them in one line

            self.usb_audio_device_names = ",".join(self.usb_device_list)
            self.lineEditAudioDevice.setText(self.usb_audio_device_names)

        except subprocess.CalledProcessError as e:
            print("Error:", e.output)




class RigControlPage(base_10, form_10):
    def __init__(self, motors, pipeline):
        super(base_10, self).__init__()
        self.setupUi(self)
        self.motors = motors
        self.pipeline = pipeline
        self.sys = systemConfig
        self.vid = systemCamera
        self.ui = systemUI

        self.resizeWindow()
        self.setIconSizes()
        self.buttonClickActions()
        self.setDialSettings()
        self.defaultSettings()

        self._motor_cmd_queue = queue.Queue()


    def defaultSettings(self):

        self.motor = "LR"
        self.control_motor_left =1
        self.control_motor_right=6
        s,p = self.motors.read_params(self.control_motor_left)

        self.lcdNumber.display(5)


    def setDialSettings(self):
        dial_size = self.ui.DIAL_SIZE
        self.dial.setFixedSize(dial_size, dial_size)

        self.dial.setMaximum(100)
        self.dial.setMinimum(1)
        self.dial.setNotchesVisible(True)
        # self.dial.setWrapping(True)
        self.dial.setValue(5)

        initial_slider_position = 50
        # self.dial.setSliderPosition(initial_slider_position)

        self.dial.valueChanged.connect(lambda: self.lcdNumber.display(str(self.dial.value())))


    def resizeWindow(self):
        self.window_width = self.ui.RIG_CONTROLLER_WINDOW_SIZE_X
        self.window_height = self.ui.RIG_CONTROLLER_WINDOW_SIZE_Y

        self.resize(self.window_width, self.window_height)


    def setIconSizes(self):

        self.buttonExit.setIconSize(ICON_SIZE*0.8)
        self.buttonmoveCCW.setIconSize(ICON_SIZE)
        self.buttonmoveCW.setIconSize(ICON_SIZE)

        self.buttonTilt.setIconSize(ICON_SIZE)
        self.buttonConvergance.setIconSize(ICON_SIZE)
        self.buttonSeperation.setIconSize(ICON_SIZE)


        self.buttonSelectLeftMotor.setIconSize(ICON_SIZE)
        self.buttonSelectRightMotor.setIconSize(ICON_SIZE)
        self.buttonSelectBothMotors.setIconSize(ICON_SIZE)
        self.buttonMoveHome.setIconSize(ICON_SIZE)
        self.buttonMoveStop.setIconSize(ICON_SIZE)

        

    def buttonClickActions(self):

        self.buttonStep_5.clicked.connect(self.buttonStep_5_clickAction)
        self.buttonStep_10.clicked.connect(self.buttonStep_10_clickAction)
        self.buttonStep_20.clicked.connect(self.buttonStep_20_clickAction)
        self.buttonStep_40.clicked.connect(self.buttonStep_40_clickAction)

        self.buttonGroupControlMotors.buttonClicked.connect(self.buttonGroupControlMotorsChangedAction)

        self.buttonGroupSelectMotor.buttonClicked.connect(self.buttonGroupSelectMotorClickedAction)

        self.buttonMoveHome.clicked.connect(self.buttonMoveHomeClickAction)
        self.buttonMoveStop.clicked.connect(self.buttonMoveStopClickAction)
        self.buttonExit.clicked.connect(self.closeEvent)

        self.buttonUp.clicked.connect(self.stepUpAction)
        self.buttonDown.clicked.connect(self.stepDownAction)

        self.buttonmoveCCW.clicked.connect(self.buttonmoveCCWClickAction)
        self.buttonmoveCW.clicked.connect(self.buttonmoveCWClickAction)

    def buttonGroupControlMotorsChangedAction(self, button):

        if button.objectName().__eq__("buttonSeperation"):
            self.control_motor_left =1
            self.control_motor_right=6

            
        if button.objectName().__eq__("buttonTilt"):
            self.control_motor_left =2
            self.control_motor_right=5


        if button.objectName().__eq__("buttonConvergance"):
            self.control_motor_left =3
            self.control_motor_right=4


        s,p = self.motors.read_params(self.control_motor_left)

        # print("speed and power",self.control_motor_left, self.control_motor_right)
        s=str(s)

        p=str(p)

    def buttonGroupSelectMotorClickedAction(self, button):

        if button.objectName().__eq__("buttonSelectLeftMotor"):

            self.motor = "L"

            pass

        if button.objectName().__eq__("buttonSelectRightMotor"):

            self.motor = "R"

            pass

        if button.objectName().__eq__("buttonSelectBothMotors"):

            self.motor = "LR"
            pass



    def buttonStep_5_clickAction(self):
        self.lcdNumber.display(5)
        self.dial.setValue(5)

    def buttonStep_10_clickAction(self):
        self.lcdNumber.display(10)
        self.dial.setValue(10)

    def buttonStep_20_clickAction(self):
        self.lcdNumber.display(20)
        self.dial.setValue(20)

    def buttonStep_40_clickAction(self):
        self.lcdNumber.display(40)
        self.dial.setValue(40)

    def buttonmoveCWClickAction(self):
    
        direction_of_motor=1

        nu_of_steps = self.lcdNumber.value()
        nu_of_steps = int(nu_of_steps)

        if self.motor == "L":
            cmd = self.motors.move_steps(m1=self.control_motor_left, move=True, direction=direction_of_motor, steps=nu_of_steps)
            pass

        elif self.motor == "R":
            cmd = self.motors.move_steps(m1=self.control_motor_right, move=True, direction=direction_of_motor, steps=nu_of_steps)
            pass

        else :
            cmd = self.motors.move_steps(m1=self.control_motor_left, m2=self.control_motor_right, move=True, direction=direction_of_motor, steps=nu_of_steps)
            pass
        
        self.sendSerialCmd(cmnd=cmd)

    def buttonmoveCCWClickAction(self):
    
        direction_of_motor=0

        nu_of_steps = self.lcdNumber.value()
        nu_of_steps = int(nu_of_steps)

        if self.motor == "L":
            cmd = self.motors.move_steps(m1=self.control_motor_left, move=True, direction=direction_of_motor, steps=nu_of_steps)
            pass

        elif self.motor == "R":
            cmd = self.motors.move_steps(m1=self.control_motor_right, move=True, direction=direction_of_motor, steps=nu_of_steps)
            pass

        else :
            cmd = self.motors.move_steps(m1=self.control_motor_left, m2=self.control_motor_right, move=True, direction=direction_of_motor, steps=nu_of_steps)
            pass


        
        self.sendSerialCmd(cmnd=cmd)




    def buttonMoveHomeClickAction(self):

        if self.motor == "L":
            cmd = self.motors.move_home(m1=self.control_motor_left)
            pass
        elif self.motor == "R":
            cmd = self.motors.move_home(m1=self.control_motor_right)
            pass
        else :
            cmd = self.motors.move_home(m1=self.control_motor_left, m2=self.control_motor_right)
            pass

        self.sendSerialCmd(cmnd=cmd)


    def buttonMoveStopClickAction(self):

        if self.motor == "L":
            cmd = self.motors.move_stop(m1=self.control_motor_left)
            pass
        elif self.motor == "R":
            cmd = self.motors.move_stop(m1=self.control_motor_right)
            pass
        else :
            cmd = self.motors.move_stop(m1=self.control_motor_left, m2=self.control_motor_right)
            pass


        self.sendSerialCmd(cmnd=cmd)


    def sendSerialCmd(self,cmnd):

        self.motors.sendSerialCommand(cmd = cmnd)

        # Base64 is a binary-to-text encoding scheme that represents binary data in an ASCII string format.
        # base64_message = base64.b64encode(cmnd).decode()
        # text = "'"+str(base64_message)+"'"
        # self.lineEditcmd.setText(text)

        


    def stepUpAction(self):
        nu_of_steps         = self.lcdNumber.value()
        if nu_of_steps <100 :
            nu_of_steps = int(nu_of_steps)+1
        self.lcdNumber.display(nu_of_steps)
        self.dial.setValue(nu_of_steps)


    def stepDownAction(self):

        nu_of_steps         = self.lcdNumber.value()

        if nu_of_steps >1 :
            nu_of_steps = int(nu_of_steps)-1
        
        self.lcdNumber.display(nu_of_steps)

        self.dial.setValue(nu_of_steps)


    def closeEvent(self, event):

        self.close()


    def openSettingsMainWindow(self):
        self.settingsWindow = SettingsPage()
        self.settingsWindow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.settingsWindow.show()


    def resizeEvent(self, event):
        
        size = self.size()
        self.x = size.width()
        self.y = size.height()

        self.ui.RIG_CONTROLLER_WINDOW_SIZE_X = self.x
        self.ui.RIG_CONTROLLER_WINDOW_SIZE_Y = self.y
        self.ui.save()


class Preset(base_20, form_20):
    def __init__(self, motors) :
        super(base_20,self).__init__()
        self.setupUi(self)
        self.motors = motors
        self.vid = systemCamera
        self.sys = systemConfig
        self.ui = systemUI
        self.resizeWindow()
        self.initPermissions()
        self.buttonActions()

        self.motor_preset_queue = queue.Queue()


    def resizeWindow(self):

        x = self.ui.PRESET_WINDOW_SIZE_X
        y = self.ui.PRESET_WINDOW_SIZE_Y

        self.resize(x,y)

    def resizeEvent(self, event):

        size = self.size()
        self.x = size.width()
        self.y = size.height()

    def resizeUpdate(self):

        self.ui.PRESET_WINDOW_SIZE_X = self.x
        self.ui.PRESET_WINDOW_SIZE_Y = self.y
        self.ui.save()

    def buttonActions(self):
        self.buttonExit.clicked.connect(self.closeEvent)

        self.buttonP1.clicked.connect(self.buttonP1_clickedAction)
        self.buttonP2.clicked.connect(self.buttonP2_clickedAction)
        self.buttonP3.clicked.connect(self.buttonP3_clickedAction)
        self.buttonP4.clicked.connect(self.buttonP4_clickedAction)
        self.buttonP5.clicked.connect(self.buttonP5_clickedAction)
        self.buttonP6.clicked.connect(self.buttonP6_clickedAction)
        self.buttonP7.clicked.connect(self.buttonP7_clickedAction)
        self.buttonP8.clicked.connect(self.buttonP8_clickedAction)
        self.buttonP9.clicked.connect(self.buttonP9_clickedAction)

        self.buttonStop.clicked.connect(self.buttonStopAction)
        
        
        self.buttonP1.setEnabled(False)
        self.buttonP2.setEnabled(False)
        self.buttonP3.setEnabled(False)
        self.buttonP4.setEnabled(False)
        self.buttonP5.setEnabled(False)
        self.buttonP6.setEnabled(False)
        self.buttonP7.setEnabled(False)
        self.buttonP8.setEnabled(False)
        self.buttonP9.setEnabled(False)

        # a is a tuple  contain availability and name
        

        a=MotorParameters().preset_availability(preset_num=1)
        if a[0] is True:
            self.buttonP1.setEnabled(True)
            if a[1] is not None:
                self.buttonP1.setText(a[1])


        a=MotorParameters().preset_availability(preset_num=2)
        if a[0] is True:
            self.buttonP2.setEnabled(True)
            if a[1] is not None:
                self.buttonP2.setText(a[1])

        a=MotorParameters().preset_availability(preset_num=3)
        if a[0] is True:
            self.buttonP3.setEnabled(True)
            if a[1] is not None:
                self.buttonP3.setText(a[1])

        a=MotorParameters().preset_availability(preset_num=4)
        if a[0] is True:
            self.buttonP4.setEnabled(True)
            if a[1] is not None:
                self.buttonP4.setText(a[1])

        a=MotorParameters().preset_availability(preset_num=5)
        if a[0] is True:
            self.buttonP5.setEnabled(True)
            if a[1] is not None:
                self.buttonP5.setText(a[1])


        a=MotorParameters().preset_availability(preset_num=6)
        if a[0] is True:
            self.buttonP6.setEnabled(True)
            if a[1] is not None:
                self.buttonP6.setText(a[1])


        a=MotorParameters().preset_availability(preset_num=7)
        if a[0] is True:
            self.buttonP7.setEnabled(True)
            if a[1] is not None:
                self.buttonP7.setText(a[1])


        a=MotorParameters().preset_availability(preset_num=8)
        if a[0] is True:
            self.buttonP8.setEnabled(True)
            if a[1] is not None:
                self.buttonP8.setText(a[1])


        a=MotorParameters().preset_availability(preset_num=9)
        if a[0] is True:
            self.buttonP9.setEnabled(True)
            if a[1] is not None:
                self.buttonP9.setText(a[1])

                
        
        

        # if  MotorParameters().preset_availability():
        #     print("available")
        #     self.buttonP1.setEnabled(True)

        #     name = MotorParameters().preset_name(preset_num=1)
        #     if name is not None:
        #         self.buttonP1.setText(name)

            

    def buttonP1_clickedAction(self):
        MotorParameters().move_preset(preset_num=1)
        pass


    def buttonP2_clickedAction(self):
        MotorParameters().move_preset(preset_num=2)
        pass

    def buttonP3_clickedAction(self):
        MotorParameters().move_preset(preset_num=3)
        pass

    def buttonP4_clickedAction(self):
        MotorParameters().move_preset(preset_num=4)
        pass

    def buttonP5_clickedAction(self):
        MotorParameters().move_preset(preset_num=5)
        pass

    def buttonP6_clickedAction(self):
        MotorParameters().move_preset(preset_num=6)
        pass

    def buttonP7_clickedAction(self):
        MotorParameters().move_preset(preset_num=7)
        pass

    def buttonP8_clickedAction(self):
        MotorParameters().move_preset(preset_num=8)
        
        pass

    def buttonP9_clickedAction(self):
        MotorParameters().move_preset(preset_num=9)
        
        pass

    def buttonStopAction(self):
        
        MotorParameters().move_end()

        
        pass

    def initPermissions(self):

        # subprocess.call(["echo {0} | sudo -S chmod o+rw {1}".format(self.sys.password, self.sys.PORT)], shell=True)
        # sleep(0.1)
        # subprocess.call(["stty {0} -F {1}".format(self.sys.BAUD_RATE, self.sys.PORT)], shell=True)
        # sleep(0.1)
        pass

        

    def closeEvent(self, event):
        self.resizeUpdate()
        self.close()
        # self.openSettingsMainWindow()

    def openSettingsMainWindow(self):
        self.settingsWindow = SettingsPage()
        self.settingsWindow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.settingsWindow.show()


class StreamKeyWindow(base_5, form_5):
    def __init__(self) :
        super(base_5,self).__init__()
        self.setupUi(self)
        # self.setGeometry(500, 150, 330, 250)
        self.setWindowTitle(" Stream Key ")
        self.vid = systemCamera
        self.sys = systemConfig
        self.ui = systemUI

        self.setCloudKey()

        x=self.ui.KEY_WINDOW_SIZE_X
        y=self.ui.KEY_WINDOW_SIZE_Y

        self.resize(x,y)

        self.lineEditLocalIPAddress.setText(self.vid.VR_ADDRESS.strip())
        self.lineEditYoutubeStreamKey.setText(self.vid.YOUTUBE_STREAM_KEY.strip())
        self.buttonSaveLocalIPAddress.clicked.connect(self.buttonVRAddressSaveClickedAction)
        self.buttonSaveGioviewTVStreamKey.clicked.connect(self.buttonCloudAPIKeySaveClickedAction)
        self.buttonSaveYoutubeStreamKey.clicked.connect(self.buttonYoutubeAPIKeySaveClickedAction)
        self.buttonClearIPAddress.clicked.connect(self.buttonClearIPAddressClickAction)
        self.buttonClearGeoviewTVStreamKey.clicked.connect(self.buttonClearGeoviewTVStreamKeyClickAction)
        self.buttonClearYoutubeStreamKey.clicked.connect(self.buttonSaveYoutubeStreamKeyClickAction)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.buttonExit.clicked.connect(self.closeEvent)

        self.buttonExit.setIconSize(ICON_SIZE*0.8)

    def setCloudKey(self):

        global STREAM_KEY

        if STREAM_KEY is not None:

            self.lineEditGeoviewTVStreamKey.setText(STREAM_KEY)

        else:
            text = " "
            self.lineEditGeoviewTVStreamKey.setText(text)

    def resizeEvent(self, event):

        window_size = self.size()
        window_height = window_size.height()
        window_width = window_size.width()
        self.ui.KEY_WINDOW_SIZE_X = window_width
        self.ui.KEY_WINDOW_SIZE_Y = window_height
        self.ui.save()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Store the initial mouse position and window position
            self.startPos = event.globalPos()
            self.windowPos = self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # Calculate the new window position based on the mouse movement
            delta = event.globalPos() - self.startPos
            self.move(self.windowPos + delta)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Clear the stored positions
            self.startPos = None
            self.windowPos = None

    
    def buttonClearIPAddressClickAction(self):
        self.lineEditLocalIPAddress.setText('')

    def buttonClearGeoviewTVStreamKeyClickAction(self):
        self.lineEditGeoviewTVStreamKey.setText('')

    def buttonSaveYoutubeStreamKeyClickAction(self):
        self.lineEditYoutubeStreamKey.setText('')

    def buttonVRAddressSaveClickedAction(self, button):
        self.vid.VR_ADDRESS = self.lineEditLocalIPAddress.text().strip()
        self.vid.save()
    
    def buttonCloudAPIKeySaveClickedAction(self, button):
        self.vid.CLOUD_STREAM_KEY = self.lineEditGeoviewTVStreamKey.text().strip()
        self.vid.save()

    def buttonYoutubeAPIKeySaveClickedAction(self, button):
        self.vid.YOUTUBE_STREAM_KEY = self.lineEditYoutubeStreamKey.text().strip()
        self.vid.save()


    def closeEvent(self, event):
        self.close()
        # self.openSettingsMainWindow()

    def openSettingsMainWindow(self):
        self.settingsWindow = SettingsPage()
        self.settingsWindow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.settingsWindow.show()


class RecordingFolderWindow(base_11, form_11):
    def __init__(self, pipeline) :
        super(base_11,self).__init__()
        self.setupUi(self)
        # self.setGeometry(500, 150, 400, 150)
        self.setWindowTitle(" Recording Path ")
        self.sys = systemConfig
        self.vid = systemCamera
        self.ui = systemUI
        self.pipeline = pipeline
        self.buttonSelectRecordSavePath.clicked.connect(self.openFolderDialog)
        self.labelRecordingPath.setText(self.vid.DROP_LOCATION)
        self.buttonExit.clicked.connect(self.closeEvent)

        self.buttonExit.setIconSize(ICON_SIZE*0.8)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Store the initial mouse position and window position
            self.startPos = event.globalPos()
            self.windowPos = self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # Calculate the new window position based on the mouse movement
            delta = event.globalPos() - self.startPos
            self.move(self.windowPos + delta)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Clear the stored positions
            self.startPos = None
            self.windowPos = None

    def closeEvent(self, event):
        self.close()      
        windowHome.show() 

    def openFolderDialog(self):
        dialog = QFileDialog(self)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        # dialog.setFileMode(QFileDialog.DirectoryOnly)
        # dialog.exec_()
        # dir_path = QFileDialog.getExistingDirectory(dialog, "Open Directory","/home", QFileDialog.DontUseNativeDialog )
        dir_path = QFileDialog.getExistingDirectory(dialog, "Open Directory","/home", QFileDialog.ShowDirsOnly )
        # check file selected or not
        if '/' in dir_path:
            dir_path = str(dir_path) + '/'
            print(dir_path)
            self.labelRecordingPath.setText(dir_path.strip())

            print(dir_path)
            self.vid.DROP_LOCATION = self.labelRecordingPath.text().strip()
            self.vid.save()
            print(dir_path)

            self.pipeline.RECORD_VIDEO_DROP_LOCATION = dir_path
        else:
            pass

        
class Camera_Settings(base_17, form_17):
    def __init__(self,pipeline) :
        super(base_17,self).__init__()

        self.setupUi(self)
        self.sys = systemConfig
        self.ui = systemUI
        # self.cam = systemCamera
        self.pipeline=pipeline
        self.camera_parameters = CameraParameters()
        self.camSettings = CameraSettings()

        self.loadSettings()
        self.settingsStatus()
        
        self.cam_params = self.camera_parameters


        self.window_size_x = self.ui.CAMERA_SETTINGS_WINDOW_SIZE_X
        self.window_size_y = self.ui.CAMERA_SETTINGS_WINDOW_SIZE_Y
        self.resize(self.window_size_x, self.window_size_y)
        
        self.buttonExitFromCamSettings.setIconSize(ICON_SIZE*0.8)

        self.update_label()

        self.AELock_checkBox.setChecked(True)
        self.AELock_checkBox.setEnabled(True)



        self.doubleSpinBoxExposure.setButtonSymbols(QSpinBox.NoButtons)
        self.doubleSpinBoxSaturation.setButtonSymbols(QSpinBox.NoButtons)

        self.comboBoxChangeAction()
        self.buttonClickActions()
        self.comboBoxClickActions()

        # try:
        #     self.listAudioDevice()
        # except:
        #     print("Unable to detect Audio Devices")

    def listAudioDevice(self):

        try:
            output = subprocess.check_output(['arecord', '-l'], stderr=subprocess.STDOUT, universal_newlines=True)
            lines = output.split('\n')
            
            usb_device_count = 0
            self.usb_device_list = []
            
            for line in lines:
                if "USB Audio Device" in line:
                    usb_device_count += 1
                    device_name = line.strip().split(":")[-1].strip()
                    self.usb_device_list.append(device_name)
            
            print(f"Total USB audio input devices detected: {usb_device_count}")
            print("List of available USB audio input device names:")
            # print("hhhh  ",self.usb_device_names)
            # print(", ".join(self.usb_device_names))  # Join the names with commas and print them in one line

            self.usb_audio_device_names = ",".join(self.usb_device_list)
            self.lineEditAudioIn.setText(self.usb_audio_device_names)

        except subprocess.CalledProcessError as e:
            print("Error:", e.output)


    def comboBoxChangeAction(self):
        self.doubleSpinBoxExposure.valueChanged.connect(self.doubleSpinBoxExposureValueChanged)
        self.doubleSpinBoxSaturation.valueChanged.connect(self.doubleSpinBoxSaturationValueChanged)

    def loadSettings(self):

        

        self.WB_MODE_Selected        = self.camSettings.WBMODE
        self.ANTI_BANDING_Selected   = self.camSettings.AEANTI_BANDING
        self.EE_MODE_Selected        = self.camSettings.EDGE_ENHANCE
        self.AWB_LOCK_Selected       = self.camSettings.AWB_LOCK
        self.AE_LOCK_Selected        = self.camSettings.AE_LOCK

        self.SATURATION              = self.camSettings.SATURATION
        self.EXPOSURE_COMPENSATION = self.camSettings.EXPOSURE_COMPENSATION
        self.TNR_MODE = self.camSettings.TNR_MODE
        # self.TNR_MODE              

        
   
        # print( self.WB_MODE_Selected,self.ANTI_BANDING_Selected, self.EE_MODE_Selected, self.AWB_LOCK_Selected , "jjjjjj")

    def settingsStatus(self):
        
        self.wbmode_comboBox.setCurrentIndex(self.WB_MODE_Selected)
        self.aeantiBanding_comboBox.setCurrentIndex(self.ANTI_BANDING_Selected)
        self.edgeEnhanceMode_comboBox.setCurrentIndex(self.EE_MODE_Selected)
        self.AwbLock_checkBox.setChecked(self.AWB_LOCK_Selected)
        self.AELock_checkBox.setChecked(self.AE_LOCK_Selected)

        self.doubleSpinBoxExposure.setMinimum(-2.00)
        self.doubleSpinBoxExposure.setMaximum(2.00)
        self.doubleSpinBoxExposure.setValue(self.EXPOSURE_COMPENSATION)

        self.doubleSpinBoxSaturation.setMinimum(0.00)
        self.doubleSpinBoxSaturation.setMaximum(2.00)
        self.doubleSpinBoxSaturation.setValue(self.SATURATION)

        self.tnrModeComboBox.setCurrentIndex(self.TNR_MODE)

    
    def buttonClickActions(self):

        self.AwbLock_checkBox.clicked.connect(self.AwbLock_checkBox_Clicked)
        self.AELock_checkBox.clicked.connect(self.AELock_checkBox_Clicked)
        self.buttonExitFromCamSettings.clicked.connect(self.closeEvent)
        self.button_camera_default.clicked.connect(self.loadDefaultCamParameters)
        self.buttonExposureDown.clicked.connect(self.exposureDown)
        self.buttonExposureUp.clicked.connect(self.exposureUp)
        self.buttonSaturationUp.clicked.connect(self.saturationUp)
        self.buttonSaturationDown.clicked.connect(self.saturationDown)

    def comboBoxClickActions(self):

        self.wbmode_comboBox.currentIndexChanged.connect(self.wbmode_comboBox_changed)
        self.aeantiBanding_comboBox.currentIndexChanged.connect(self.aeantiBanding_comboBox_changed)
        self.edgeEnhanceMode_comboBox.currentIndexChanged.connect(self.EdgeEnhanceMode_comboBox_changed)
        self.tnrModeComboBox.currentIndexChanged.connect(self.tnrModeComboBox_changed_action)
        

    def update_label(self):
        # Get the current window size
        window_size = self.size()
        self.window_size_x = window_size.width()
        self.window_size_y = window_size.height()
        # Set the text of the label to display the window size
        # self.label_size.setText(f"Window size: {self.window_size_x} x {self.window_size_y}")
        
    def resizeEvent(self, event):
        self.update_label()

    def saveWindowSizeCamSettings(self):
        
        self.ui.CAMERA_SETTINGS_WINDOW_SIZE_X = self.window_size_x
        self.ui.CAMERA_SETTINGS_WINDOW_SIZE_Y = self.window_size_y
        self.ui.save()
        pass

    

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Store the initial mouse position and window position
            self.startPos = event.globalPos()
            self.windowPos = self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # Calculate the new window position based on the mouse movement
            delta = event.globalPos() - self.startPos
            self.move(self.windowPos + delta)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Clear the stored positions
            self.startPos = None
            self.windowPos = None

    def AwbLock_checkBox_Clicked(self):

        prop = 'awblock'
        if self.AwbLock_checkBox.isChecked():
            self.pipeline.ChangePipelineParameters(property=prop , mode=True)
            # self.AWB_LOCK_Selected = True
            self.camSettings.AWB_LOCK = True
            self.camSettings.save()
        else:
            self.pipeline.ChangePipelineParameters(property=prop , mode=False)
            # self.AWB_LOCK_Selected = False
            self.camSettings.AWB_LOCK = False
            self.camSettings.save()

        

    def AELock_checkBox_Clicked(self):

        prop = 'aelock'
        if self.AELock_checkBox.isChecked():
            self.pipeline.ChangePipelineParameters(property=prop , mode=True)
            # AE_LOCK_Selected=True
        else:
            self.pipeline.ChangePipelineParameters(property=prop , mode=False)
            # AE_LOCK_Selected=False

    def wbmode_comboBox_changed(self):
        
        selected_value = self.wbmode_comboBox.currentText()

        prop = 'wbmode'

        modes = {  
                    "Off" :             0,
                    "Auto":             1,
                    "Incandescent":     2,
                    "Fluorescent":      3,
                    "warm-fluorescent": 4,
                    "daylight":         5,
                    "cloudy-daylight":  6,
                    "twilight":         7,
                    "shade":            8,
                    "manual":           9
                }       
        mode = modes.get(selected_value)
        if mode is not None:
            self.pipeline.ChangePipelineParameters(property=prop, mode=mode)
        
        # global WB_MODE_Selected
        # self.WB_MODE_Selected = selected_value

        self.camSettings.WBMODE = mode

        self.camSettings.save()
        
    def aeantiBanding_comboBox_changed(self):

        selected_value = self.aeantiBanding_comboBox.currentText()
        prop='aeantibanding'

        modes = {
                    "Off"   :0 , 
                    "Auto"  :1 ,
                    "50Hz"  :2 ,
                    "60Hz"  :3
                }
        
        mode = modes.get(selected_value)
        if mode is not None:
            self.pipeline.ChangePipelineParameters(property=prop, mode=mode)

        # global ANTI_BANDING_Selected
        # self.ANTI_BANDING_Selected = selected_value

        self.camSettings.AEANTI_BANDING = mode
        self.camSettings.save()



    def EdgeEnhanceMode_comboBox_changed(self):
        
        selected_value = self.edgeEnhanceMode_comboBox.currentText()
        prop = 'ee-mode'

        modes = {
                    "Off"         : 0,
                    "Fast"        : 1,
                    "HighQuality" : 2

                }

        mode = modes.get(selected_value)
        if mode is not None:
            self.pipeline.ChangePipelineParameters(property=prop, mode=mode)
        # global EE_MODE_Selected
        # self.EE_MODE_Selected = selected_value

        self.camSettings.EDGE_ENHANCE = mode
        self.camSettings.save()

    def tnrModeComboBox_changed_action(self):

        selected_value = self.tnrModeComboBox.currentText()
        prop = 'tnr-mode'

        modes = {
                    "Off"         : 0,
                    "Fast"        : 1,
                    "HighQuality" : 2

                }
        
        mode = modes.get(selected_value)
        if mode is not None:
            self.pipeline.ChangePipelineParameters(property=prop, mode=mode)

        self.camSettings.TNR_MODE = mode
        self.camSettings.save()


    def doubleSpinBoxExposureValueChanged(self):

        currentValue = self.doubleSpinBoxExposure.value()

        if currentValue == 2.00 or currentValue == -2.00:
            pass
        else:
            prop = 'exposurecompensation'
            self.pipeline.ChangePipelineParameters(property=prop, mode=currentValue)

        self.camSettings.EXPOSURE_COMPENSATION = currentValue
        self.camSettings.save()


    def doubleSpinBoxSaturationValueChanged(self):

        currentValue = self.doubleSpinBoxSaturation.value()

        if currentValue == 0.00 or currentValue == 2.00:
            pass
        else:
            prop = 'saturation'
            self.pipeline.ChangePipelineParameters(property=prop, mode=currentValue)

        self.camSettings.SATURATION = currentValue
        self.camSettings.save()


    def loadDefaultCamParameters(self):



        # WBMODE_DEFAULT                  = 1
        # AEANTI_BANDING_DEFAULT          = 1
        # EDGE_ENHANCE_DEFAULT            = 0
        # AWB_LOCK_DEFAULT                = False
        # EXPOSURE_COMPENSATION_DEFAULT   = 0.00
        # SATURATION_DEFAULT              = 1.00
        # TNR_MODE_DEFAULT                = 1


        WBMODE_DEFAULT                  = self.camSettings.WBMODE_DEFAULT
        AEANTI_BANDING_DEFAULT          = self.camSettings.AEANTI_BANDING_DEFAULT
        EDGE_ENHANCE_DEFAULT            = self.camSettings.EDGE_ENHANCE_DEFAULT
        AWB_LOCK_DEFAULT                = self.camSettings.AWB_LOCK_DEFAULT
        EXPOSURE_COMPENSATION_DEFAULT   = self.camSettings.EXPOSURE_COMPENSATION_DEFAULT
        SATURATION_DEFAULT              = self.camSettings.SATURATION_DEFAULT
        TNR_MODE_DEFAULT                = self.camSettings.TNR_MODE_DEFAULT




        self.wbmode_comboBox.setCurrentIndex(WBMODE_DEFAULT)
        self.aeantiBanding_comboBox.setCurrentIndex(AEANTI_BANDING_DEFAULT)
        self.edgeEnhanceMode_comboBox.setCurrentIndex(EDGE_ENHANCE_DEFAULT)
        # self.AELock_checkBox.setChecked(False)
        self.AwbLock_checkBox.setChecked(AWB_LOCK_DEFAULT)
        self.doubleSpinBoxExposure.setValue(EXPOSURE_COMPENSATION_DEFAULT)
        self.doubleSpinBoxSaturation.setValue(SATURATION_DEFAULT)
        self.tnrModeComboBox.setCurrentIndex(TNR_MODE_DEFAULT)

        self.camSettings.WBMODE                 = WBMODE_DEFAULT
        self.camSettings.AEANTI_BANDING         = AEANTI_BANDING_DEFAULT
        self.camSettings.EDGE_ENHANCE           = EDGE_ENHANCE_DEFAULT
        self.camSettings.AWB_LOCK               = AWB_LOCK_DEFAULT
        self.camSettings.EXPOSURE_COMPENSATION  = EXPOSURE_COMPENSATION_DEFAULT
        self.camSettings.SATURATION             = SATURATION_DEFAULT
        self.camSettings.TNR_MODE               = TNR_MODE_DEFAULT

        self.camSettings.save()

        

    def exposureUp(self):

        value = self.doubleSpinBoxExposure.value()
        value = value + 0.20
        self.doubleSpinBoxExposure.setValue(value)
        pass

    def exposureDown(self):

        value = self.doubleSpinBoxExposure.value()
        value = value - 0.20
        self.doubleSpinBoxExposure.setValue(value)
        print(value)
        pass

    def saturationUp(self):

        value = self.doubleSpinBoxSaturation.value()
        value = value + 0.2
        self.doubleSpinBoxSaturation.setValue(value)
        

    def saturationDown(self):

        value = self.doubleSpinBoxSaturation.value()
        value = value - 0.2
        self.doubleSpinBoxSaturation.setValue(value)


    def displayExposure(self):

 
        variable = 'exposure'
        command = f'v4l2-ctl -d /dev/video0 -C {variable}'
        output = subprocess.check_output(command, shell=True)
        output_str = output.decode('utf-8')
        variable=variable +':'
        new_text = output_str.replace(variable, "")
        new_text = new_text.strip()
        self.labelExposure.setText(new_text)

    def displayGain(self):


        variable = 'gain'
        command = f'v4l2-ctl -d /dev/video0 -C {variable}'
        output = subprocess.check_output(command, shell=True)
        output_str = output.decode('utf-8')
        variable=variable +':'
        new_text = output_str.replace(variable, "")
        new_text = new_text.strip()
        self.labelGain.setText(new_text)



    def closeEvent(self ,event):
        self.saveWindowSizeCamSettings()
        self.close()
        # self.openSettingsMainWindow()

    def openSettingsMainWindow(self):
        self.settingsWindow = SettingsPage()
        self.settingsWindow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.settingsWindow.show()


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$444444444444444444444444444444444444444444444444


class FileManagerWindow(base_13, form_13):
    def __init__(self) :
        super(base_13,self).__init__()
        self.setupUi(self)


        self.buttonSelectPath.clicked.connect(self.buttonSelectPathClickAction)
        self.buttonMoveFiles.clicked.connect(self.buttonMoveFilesClickAction)
        self.buttonExitFileManager.clicked.connect(self.closeEvent)

        self.buttonExitFileManager.setIconSize(ICON_SIZE*0.8)

    def buttonSelectPathClickAction(self):
        self.windowServer = RecordingFolderWindow(cm)
        self.windowServer.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.close()
        self.windowServer.resize(int(screen_width/2),int(screen_height/4))
        self.windowServer.show()
        pass

    def buttonMoveFilesClickAction(self):

        self.windowServer = FileMoveWindow()
        self.windowServer.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.close()
        self.windowServer.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Store the initial mouse position and window position
            self.startPos = event.globalPos()
            self.windowPos = self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # Calculate the new window position based on the mouse movement
            delta = event.globalPos() - self.startPos
            self.move(self.windowPos + delta)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Clear the stored positions
            self.startPos = None
            self.windowPos = None

    def closeEvent(self, event):
        self.close()
        # self.openSettingsMainWindow()

    def openSettingsMainWindow(self):
        self.settingsWindow = SettingsPage()
        self.settingsWindow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.settingsWindow.show()


class FileMoveWindow(base_14, form_14):
    def __init__(self) :
        super(base_14,self).__init__()
        self.setupUi(self)
        self.vid = systemCamera

        self.buttonSelect.clicked.connect(self.select_file)
        self.buttonCopy.clicked.connect(self.select_copy)
        self.buttonDelete.clicked.connect(self.select_delete)
        
        self.listWidget.itemClicked.connect(self.getItem)
        self.buttonExitFromCopy.clicked.connect(self.closeEvent)

        self.buttonExitFromCopy.setIconSize(ICON_SIZE*0.8)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Store the initial mouse position and window position
            self.startPos = event.globalPos()
            self.windowPos = self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # Calculate the new window position based on the mouse movement
            delta = event.globalPos() - self.startPos
            self.move(self.windowPos + delta)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Clear the stored positions
            self.startPos = None
            self.windowPos = None

    def getItem(self, lstItem):

        name = lstItem.text()
        lstItem.setSelected(True)

        for i in range(len(self.filenames)):
            element = self.filenames[i]
            filename = os.path.basename(element)
            if name == filename:
               self.ara.append(element)
       
  
    


    def select_file(self):

        self.filenames, _  = QFileDialog.getOpenFileNames(self,"Open Single File","{0}".format(self.vid.DROP_LOCATION),"Videos (*.mp4)")

        self.namelist = []
        self.listWidget.clear()

        for i in range(len(self.filenames)):
            element = self.filenames[i]
            filename = os.path.basename(element)
            self.namelist.append(filename)

        self.listWidget.addItems(self.namelist)
   
    def select_copy(self):

        USBdrivername = QFileDialog.getExistingDirectory(self, "Open Directory")

        for i in range(len(self.filenames)):
        # Access the ith element of the array
            element = self.filenames[i]
            filename = os.path.basename(element)
            locaton = USBdrivername
            dst =locaton+'/'+filename
            shutil.copy(src=element, dst=dst)
            self.listWidget.clear()
        self.listWidget.addItem("Files Transferring...")        
        filepath = os.path.join(USBdrivername, filename)

        while not os.path.exists(filepath):
            print(f"The file {filename} is not available yet.")
            time.sleep(0.1) # wait for 1 second before checking again

        self.listWidget.clear()
        self.listWidget.addItem("Files Transferring Completed")

    def select_delete(self):
   
        aralistss = self.filenames
        for file_path in aralistss:
            os.remove(file_path)
            print(f'Deleted file: {file_path}')
        
        self.listWidget.clear()
        self.listWidget.addItem('Files Deleted successfully')

    def closeEvent(self, event):
        self.close()      
        windowHome.show() 


class BlackWindow(base_15, form_15):
    def __init__(self) :
        super(base_15,self).__init__()
        self.setupUi(self)
        self.setWindowTitle("  ")
        self.ui = systemUI

        self.setBackgroundImage()

    def setBackgroundImage(self):

        try:
            image_path = self.ui.BACKGROUNG_IMAGE
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, (screen_width,screen_height))
            h, w, ch = image.shape
            q_img = QImage(image.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            self.labelBackgroundImage.setPixmap(pixmap)

        except:
            print("Unable to view Background Image")



class ExitConfirmWindow(base_16, form_16):
    def __init__(self, pipeline):
        super(base_16,self).__init__()
        self.setupUi(self)   
        self.pipeline = pipeline
        self.sys = systemConfig
        self.ui = systemUI
        self.buttonShutDown.clicked.connect(self.shutdownAction)
        self.buttonRestart.clicked.connect(self.restartAction)
        self.burronCloseApp.clicked.connect(self.closeAppAction)
        self.buttonNo.clicked.connect(self.noAction)

        self.buttonShutDown.setIconSize(ICON_SIZE)
        self.buttonRestart.setIconSize(ICON_SIZE)
        self.burronCloseApp.setIconSize(ICON_SIZE)
        self.buttonNo.setIconSize(ICON_SIZE*0.8)

        self.burronCloseApp.setVisible(False)
        self.label_3.setVisible(False)

        self.processTimer = Timer

        if not self.sys.ENABLE_CLOSE_APP_BUTTON :
            self.burronCloseApp.setVisible(False)
            self.label_3.setVisible(False)

        # self.exitKeyCombination()

    def exitKeyCombination(self):

        def on_key_release(key):
            if key == keyboard.Key.ctrl_l:
                global ctrl_pressed
                ctrl_pressed = False
            if key == keyboard.Key.alt_l:
                global alt_pressed
                alt_pressed = False
            if key == keyboard.KeyCode.from_char('k') and ctrl_pressed and alt_pressed:
                print("Ctrl+Alt+K detected!")

        def on_key_press(key):
            if key == keyboard.Key.ctrl_l:
                global ctrl_pressed
                ctrl_pressed = True
            if key == keyboard.Key.alt_l:
                global alt_pressed
                alt_pressed = True

        ctrl_pressed = False
        alt_pressed = False

        with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as listener:
            listener.join()
                

    def shutdownAction(self):
        try:

            subprocess.call(["echo {0} | sudo -S shutdown -h now".format(self.sys.password)], shell=True)
       

        except:
            print("Unable to execute shutdown command")
    
    def restartAction(self):

        try:
            subprocess.call(["echo {0} | sudo -S reboot".format(self.sys.password)], shell=True)
        
        except:

            print(" Unable to Execute Reboot command")

    def closeAppAction(self):

        self.pipeline.stop_preview()
        app.quit()

    def pushButtonAction(self):

        self.pipeline.stop_preview()
        self.startProcess()
        app.quit()

    def startProcess(self):

        def sss():
            self.open_app()
        t = self.processTimer(5 ,sss)
        t.start()


    def open_app(self):


        directory='/media/nvidia/GIOVIEW1/3DV'
        app_name='./app'
        # open a new terminal window
        subprocess.Popen(['gnome-terminal'])

        # change the directory in the terminal
        cd_command = 'cd "{}"'.format(directory)
        app_command = './{}'.format(app_name)
        full_command = '{} && {}'.format(cd_command, app_command)

        subprocess.Popen(['gnome-terminal', '-x', 'bash', '-c', full_command])


    def noAction(self):
        
        self.close()
        windowHome.show() 
        pass


if __name__=='__main__':
    app=QApplication(sys.argv)
    
    screen = app.primaryScreen()
    Main_Window_Geometry = screen.availableGeometry()
    screen_height = Main_Window_Geometry.height()
    screen_width = Main_Window_Geometry.width()

    from controls.settings import Camera, System, CameraSettings, MotorPresets, AISettings, UI, AudioSettings
    # from controls.remotecontrol import RemoteControler

    # new = System(screen_w=15)
    systemConfig = System()
    systemUI = UI(screen_w=screen_width)
    systemCamera = Camera()
    audioConfig = AudioSettings()

    # x= int(screen_width/30)
    x = systemUI.ICON_SIZE
    ICON_SIZE = QSize(x, x)

    print(screen_width, screen_height)

    mp = MotorParameters()
    cp = CameraParameters()
    cm = CameraStreamer()

    windowHome = MainWindow(cm, mp) 
    windowHome.move(0 ,(screen_height))
    # windowHome.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint )

    windowHome.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    windowHome.setWindowFlags(windowHome.windowFlags() & ~Qt.WindowCloseButtonHint)
    windowHome.show()
    sys.excepthook = system_shudown_hook
    sys.exit(app.exec())
