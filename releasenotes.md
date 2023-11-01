24-June-2023
	01. Camera positionning presets added
	
26-June-2023
	01. Jetson Clocks disabling bug fixed
	02. H265 Higher FPS 4K@40FPS, FHD@70FPS, HD@100FPS
	02. Improved H265 4K pipeline for frame synchronization and lesser frame dropping
	
27-June-2023
	01. Rig Controller UI changed
	02. Communication port updated
	
	
07-June-2023
	01. Added vertical Calibration to Blended Preview
	02. Added AI Button

08-June-2023
	01. Added Peer to Peer Local Streaming
	02. Vertical Calibration PID aggresive parameters increased
	03. Added TNR mode in camera settings
	
12-June-2023
	01. Added 3D preview modes
		1. CheckerBoard
		2. SBS
		3. Anaglyph

14-July-2023
	01. Frame synchronizing modified.
	
17-July-2023
	01. Frame synchronization forced in H265 recording pipeline
	
19-July-2023
	01. H265 and H264 Recording Frame synchronization fixed (Pending Confirmation)
	02. Audio track removed

20-July-2023
	01. H265/H264 Recording configurable FPS through camera.yaml enabled
	02. Enhanced pipelines to handle bufferring before compositor
	03. Reduced bitrate to 25Mbps and set Multiqueue defaults 
	04. Compositor sync forced. QOS Event Trigger enabled for capturing frame droppings. Additional buffering enabled before compositor.
	05. As camera sync is not enabled in camera drivers, camera sync forced using multiqueue sync with running time

21-July-2023 ******* FRAMES SYNCHRONIZED ******
	01. Maximized preview frames
	02. Recoding pipeline parser caps filter corrected
	03. CAMERA do-timestamp=true, multiqueue sync-by-running-time=true use-buffering=true

22-July-2023
	01. On pipeline error pipeline stop button activated
	02. Active pipelines can stop with shutdown button
	03. yaml files moved to the config folder
	04. Audio chanel added to recording h265/h264
	
	
	
04-Aug-2023
	01. New streaming endpoint enabled
	
	
	
08-Aug-2023 
	01. Added zero point calibration
	02. Added separate window for calibration 
	
	
	
08-Aug-2023_v2
	01. Removed QP range from rtmp-h264 streaming
	

11-Aug-2023
	01. Fixed issues in Auto Calibration
	
	
07-Sep-2023
	01. Added 3D level adjustment buttons to AI Window
	02. Added Jetson App autostart
	
	
	
	


Issue : need to restart app to Record videos after changing the recording path
	Fixed
	14-03-2023
		
		
