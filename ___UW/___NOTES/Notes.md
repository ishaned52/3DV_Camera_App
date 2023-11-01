ppnvgstplayer-1.0 -i /media/nvidia/Gioview/Recordings/HD_STEREO_2022_11_25-13:16:23.mp4

pyinstaller --clean -n app app.py


hide close button
https://www.programcreek.com/python/example/101603/PyQt5.QtCore.Qt.WindowContextHelpButtonHint




Error generated. /dvs/git/dirty/git-master_linux/multimedia/nvgstreamer/gst-nvarguscamera/gstnvarguscamerasrc.cpp, execute:762 Failed to create CaptureSession
CONSUMER: ERROR OCCURRED
ERROR: nvarguscamerasrc0 : DISCONNECTED




thursday 26/01/2022
--------------------------


Using winsys: x11 
GST_ARGUS: Creating output stream
GST_ARGUS: Creating output stream
CONSUMER: Waiting until producer is connected...
GST_ARGUS: Available Sensor modes :
GST_ARGUS: 3840 x 2160 FR = 36.999999 fps Duration = 27027028 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;

GST_ARGUS: 3840 x 2160 FR = 44.000001 fps Duration = 22727272 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;

GST_ARGUS: 1944 x 1096 FR = 70.000001 fps Duration = 14285714 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;

GST_ARGUS: 1296 x 732 FR = 103.999996 fps Duration = 9615385 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;

GST_ARGUS: Running with following settings:
   Camera index = 0 
   Camera mode  = 0 
   Output Stream W = 3840 H = 2160 
   seconds to Run    = 0 
   Frame Rate = 36.999999 
GST_ARGUS: Setup Complete, Starting captures for 0 seconds
GST_ARGUS: Starting repeat capture requests.
CONSUMER: Producer has connected; continuing.
CONSUMER: Waiting until producer is connected...
GST_ARGUS: Available Sensor modes :
GST_ARGUS: 3840 x 2160 FR = 36.999999 fps Duration = 27027028 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;

GST_ARGUS: 3840 x 2160 FR = 44.000001 fps Duration = 22727272 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;

GST_ARGUS: 1944 x 1096 FR = 70.000001 fps Duration = 14285714 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;

GST_ARGUS: 1296 x 732 FR = 103.999996 fps Duration = 9615385 ; Analog Gain range min 1.000000, max 31.622776; Exposure Range min 450000, max 200000000;

GST_ARGUS: Running with following settings:
   Camera index = 1 
   Camera mode  = 0 
   Output Stream W = 3840 H = 2160 
   seconds to Run    = 0 
   Frame Rate = 36.999999 
GST_ARGUS: Setup Complete, Starting captures for 0 seconds
GST_ARGUS: Starting repeat capture requests.
CONSUMER: Producer has connected; continuing.


gst-launch-1.0 nvarguscamerasrc sensor-id=<n> ! "video/x-raw(memory:NVMM), width=(int)1944 height=(int)1096, format=(string)NV12" ! nvvidconv left=8 right=1928 top=8 bottom=1088 ! "video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080, format=(string)NV12" ! nv3dsink -e




Yes, you can use the pgrep and pkill commands to find and kill processes that match a particular name or pattern.

For example, if you want to kill all running GStreamer processes, you can use the following command:

ruby

$ pkill -f gst

This will find and kill all processes that have "gst" in their command line arguments or in their process name.

If you want to be more specific and only kill processes that match a certain pattern, you can modify the command accordingly. For example, if you want to kill processes that match a certain pipeline string, you can use a command like this:

ruby

$ pkill -f "nvarguscamerasrc sensor-id=0 !"

This will find and kill all processes that have the string "nvarguscamerasrc sensor-id=0 !" in their command line arguments or in their process name.

Be careful when using the pkill command, as it will kill all processes that match the specified pattern without confirmation. Make sure to use it with caution, and double-check the pattern before running the command.