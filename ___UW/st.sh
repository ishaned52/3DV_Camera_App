#!/bin/bash

gst-launch-1.0 -e  multiqueue name=mqueue sync-by-running-time=true use-buffering=true \
                    nvcompositor name=comp \
                        sink_0::interpolation-method=Smart sink_0::xpos=0 sink_0::ypos=0 sink_0::width=960 sink_0::height=1080 \
                        sink_1::interpolation-method=Smart sink_1::xpos=960 sink_1::ypos=0 sink_1::width=960 sink_1::height=1080 ! queue2 ! tee name=t0 \
                                t0. ! queue2 ! videorate skip-to-first=1 ! "video/x-raw(memory:NVMM), framerate=(fraction)30/1" ! nv3dsink sync=0 async=0 window-x=0 window-y=0 window-width=3840 window-height=2160 \
                                t0. ! queue2 ! videorate skip-to-first=1 ! "video/x-raw(memory:NVMM), framerate=(fraction)30/1"  \
                                    ! nvvidconv compute-hw=1 ! "video/x-raw(memory:NVMM), format=(string)I420" ! queue2 ! nvv4l2h264enc \
                                                    bitrate=8000000 insert-aud=1 iframeinterval=30 idrinterval=60 \
                                                        ! h264parse ! flvmux name=mux streamable=1 ! queue2 ! rtmpsink location=rtmp://39e423d77154.global-contribute.live-video.net/app/sk_ap-northeast-1_o38D3KlE6kCR_WxteZOKNSEs5J8ieoCAeXCD3qgYmsc pulsesrc do-timestamp=1 provide-clock=false ! "audio/x-raw" ! queue2 ! audioconvert ! queue2 ! audioresample ! queue2 ! voaacenc bitrate=128000 ! queue2 ! mux. \
        nvarguscamerasrc sensor-id = 0  wbmode = 1 aeantibanding = 1 ee-mode = 0 awblock = false aelock = false exposurecompensation = 0.0 saturation = 1.0 tnr-mode = 1 name = source1 do-timestamp = 1 sensor-mode=2 \
        ! "video/x-raw(memory:NVMM), width=(int)1944, height=(int)1096, format=(string)NV12, framerate=(fraction)30/1"  ! nvvidconv compute-hw=1 top=8 bottom=1088 left=12 right=1932  ! mqueue.sink_1 mqueue.src_1 ! comp. \
        nvarguscamerasrc sensor-id = 1  wbmode = 1 aeantibanding = 1 ee-mode = 0 awblock = false aelock = false exposurecompensation = 0.0 saturation = 1.0 tnr-mode = 1 name = source2 do-timestamp = 1 sensor-mode=2 \
        ! "video/x-raw(memory:NVMM), width=(int)1944, height=(int)1096, format=(string)NV12, framerate=(fraction)30/1"  ! nvvidconv compute-hw=1 top=8 bottom=1088 left=12 right=1932  ! mqueue.sink_2 mqueue.src_2 ! comp. 