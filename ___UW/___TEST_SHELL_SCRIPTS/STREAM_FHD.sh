#!/bin/bash
<<comment
01. CAMERA CAPABILITIES
sensor-mode 0 => GST_ARGUS: 3840 x 2160 FR = 36.999999 fps Duration = 27027028 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
sensor-mode 1 => GST_ARGUS: 3840 x 2160 FR = 44.000001 fps Duration = 22727272 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
sensor-mode 2 => GST_ARGUS: 1944 x 1096 FR = 70.000001 fps Duration = 14285714 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;
sensor-mode 3 => GST_ARGUS: 1296 x  732 FR =103.999996 fps Duration =  9615385 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;

4K/2160p @ 30fps 3840x2160 13000-34000Kbps Not allowed on frankkamalnonis (restricted to HD)
   1440p @ 30fps 2560x1440  6000-13000Kbps 9000Kbps
   1080p @ 30fps 1920x1080  3000- 6000Kbps
comment
L_CAM=0
R_CAM=1



CAPTURE_W=3840
CAPTURE_H=2160

FPS=30

PREVIEW_W=1920
PREVIEW_H=1080

BIT_RATE=8500000

#youtube kapraautomation
#API_KEY="060w-amru-566y-kys3-1t3h"
#TARGET_LOCATION="rtmp://a.rtmp.youtube.com/live2/$API_KEY app=live2"

API_KEY="sk_ap-northeast-1_TFQVDKAsCWYn_ZK5ClG4HxOgSG8WaDyPGicl5upYRbD"
TARGET_LOCATION="rtmps://39e423d77154.global-contribute.live-video.net:443/app/$API_KEY"

<<comment
03. EXECUTING PIPELINE
18,30:18,30:18,30
24,24:28,28:30,30
comment

gst-launch-1.0 -e \
nvcompositor name=comp \
	sink_0::interpolation-method=4 sink_0::xpos=0 sink_0::ypos=0 sink_0::width=$(expr $PREVIEW_W / 2) sink_0::height=${PREVIEW_H} \
	sink_1::interpolation-method=4 sink_1::xpos=$(expr $PREVIEW_W / 2) sink_1::ypos=0 sink_1::width=$(expr $PREVIEW_W / 2) sink_1::height=${PREVIEW_H} ! nvvidconv ! "video/x-raw(memory:NVMM), format=(string)I420" \
		! queue2 ! nvv4l2h264enc \
				qp-range="18,30:18,30:18,30" \
				control-rate=0 ! queue2 ! tee name=t0 \
			t0. ! queue2 ! nvv4l2decoder ! queue2 ! nvegltransform ! queue2 ! nveglglessink sync=false async=false \
			t0. ! queue2 ! "video/x-h264, stream-format=(string)byte-stream" ! h264parse ! queue2 ! flvmux streamable=true name=mux ! queue2 ! rtmpsink sync=false async=false location="${TARGET_LOCATION}" pulsesrc do-timestamp=true provide-clock=false ! "audio/x-raw" ! queue2 ! audioconvert ! audioresample ! voaacenc bitrate=128000 ! queue2 ! mux. \
nvarguscamerasrc sensor-id=0 sensor-mode=0 ! "video/x-raw(memory:NVMM), format=(string)NV12, width=(int)${CAPTURE_W}, height=(int)${CAPTURE_H}, framerate=(fraction)${FPS}/1" ! queue2 ! nvvidconv ! "video/x-raw(memory:NVMM), format=(string)NV12" ! nvvidconv ! "video/x-raw(memory:NVMM), format=(string)RGBA" ! comp. \
nvarguscamerasrc sensor-id=1 sensor-mode=0 ! "video/x-raw(memory:NVMM), format=(string)NV12, width=(int)${CAPTURE_W}, height=(int)${CAPTURE_H}, framerate=(fraction)${FPS}/1" ! queue2 ! nvvidconv ! "video/x-raw(memory:NVMM), format=(string)NV12" ! nvvidconv ! "video/x-raw(memory:NVMM), format=(string)RGBA" ! comp.
