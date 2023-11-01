#!/bin/bash
<<comment
01. CAMERA CAPABILITIES
sensor-mode 0 => GST_ARGUS: 3840 x 2160 FR = 36.999999 fps Duration = 27027028 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
sensor-mode 1 => GST_ARGUS: 3840 x 2160 FR = 44.000001 fps Duration = 22727272 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
sensor-mode 2 => GST_ARGUS: 1944 x 1096 FR = 70.000001 fps Duration = 14285714 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
sensor-mode 3 => GST_ARGUS: 1296 x  732 FR =103.999996 fps Duration =  9615385 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
comment
L_CAM=0
R_CAM=1

CAPTURE_W=3840
CAPTURE_H=2160
FPS=30

<<comment
02. AUDIO DEVICE SETTINGS
comment

<<comment
03. TARGET CAPTURE FILE
comment
TIMESTAMP=$(date "+%Y-%m-%d_%H%M%S")
TARGET_LOCATION="./recordings/REC_${TIMESTAMP}_H264.mp4"

<<comment
05. EXECUTING PIPELINE
comment

gst-launch-1.0 -e nvcompositor name=comp \
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=1920 sink_0::height=2160 \
sink_1::xpos=1920 sink_1::ypos=0 sink_1::width=1920 sink_1::height=2160 ! queue2 ! tee name=t0  \
t0. ! queue2 ! "video/x-raw(memory:NVMM), framerate=(fraction)30/1" ! nv3dsink sync=0 async=0 \
t0. ! queue2 ! "video/x-raw(memory:NVMM), framerate=(fraction)30/1" ! nvvidconv ! "video/x-raw(memory:NVMM), format=(string)I420" 
! queue2 ! nvvidconv ! nvjpegenc ! rndbuffersize max=65000 ! queue2 ! udpsink host=192.168.1.106 port=3001 sync=0 async=0 \
nvarguscamerasrc sensor-id=1 name=source1 sensor-mode=0 ! "video/x-raw(memory:NVMM), width=(int)3840, height=(int)2160, format=(string)NV12, framerate=(fraction)30/1"  ! nvvidconv  ! comp. \
nvarguscamerasrc sensor-id=0 name=source2 sensor-mode=0 ! "video/x-raw(memory:NVMM), width=(int)3840, height=(int)2160, format=(string)NV12, framerate=(fraction)30/1"  ! nvvidconv  ! comp. \

<<commment
nvgstplayer-1.0 -i ./REC_2023-01-30_150723.mp4
commment
