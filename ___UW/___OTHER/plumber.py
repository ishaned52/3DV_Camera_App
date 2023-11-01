import os
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib
from datetime import datetime

from controls.settings import Camera
from workers.worker_calibrator import Calibrator

# gst-launch-1.0 nvv4l2camerasrc device=/dev/video0 ! "video/x-raw(memory:NVMM), format=(string)UYVY, width=(int)1920, height=(int)1080, framerate=(fraction)75/1" ! nvvidconv ! nvegltransform ! nveglglessink

'''
video/x-raw, format=(string)UYVY, width=(int)4192, 	height=(int)3120, 	framerate=(fraction)19/1;
video/x-raw, format=(string)UYVY, width=(int)4096, 	height=(int)2160, 	framerate=(fraction)28/1;
video/x-raw, format=(string)UYVY, width=(int)3840, 	height=(int)2160, 	framerate=(fraction)30/1;
video/x-raw, format=(string)UYVY, width=(int)1920, 	height=(int)1080, 	framerate=(fraction)75/1;
video/x-raw, format=(string)UYVY, width=(int)1280, 	height=(int)720, 	framerate=(fraction)80/1;
video/x-raw, format=(string)UYVY, width=(int)640, 	height=(int)480, 	framerate=(fraction)120/1;
'''

class PipelineMaster:
	# pipeline 	= None
	# main_loop	= None
	# log 		= None
	# recbin		= None
	
	def __init__(self):
		Gst.init()

		# primary camera settings
		self.rec_4k			= False
		self.cam_selected	= "STEREO"
		self.cap_width 		= 1920
		self.cap_height		= 1080
		self.cap_fps		= 30 #50
		self.cam_alpha		= 0.5
		self.cam 			= Camera()

		# required parallel workers
		self.caibrator 		= Calibrator()
		
		# master pipeline elements
		self.main_loop 		= GLib.MainLoop()
		self.pipeline		= None
		self.recbin			= None
		self.enc 			= None
		self.mux 			= None
		self.rtmpsink		= None
		self.udpsink 		= None
		self.filesink		= None
		self.previewSink	= None
		self.tee 			= Gst.ElementFactory.make("tee")
		

	# CREATE PRIMARY PIPELINES *********************************************************************
	def leftCamPreview(self):
		if self.pipeline is None:
			# assign selected camera
			self.cam_selected="LEFT"

			self.pipeline = Gst.Pipeline.new("left cam preview")

			caps_1 = Gst.ElementFactory.make("capsfilter")
			caps_1.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)UYVY,width=(int){0},height=(int){1},framerate=(fraction){2}/1".format(str(self.cap_width), str(self.cap_height), str(self.cap_fps))))
			
			# caps_2 = Gst.ElementFactory.make("capsfilter")
			# caps_2.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)UYVY,width=(int){0},height=(int){1},framerate=(fraction){2}/1".format(str(self.cap_width), str(self.cap_height), str(self.cap_fps))))

			caps_3 = Gst.ElementFactory.make("capsfilter")
			caps_3.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)RGBA"))
			
			# caps_4 = Gst.ElementFactory.make("capsfilter")
			# caps_4.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)RGBA"))

			caps_5 = Gst.ElementFactory.make("capsfilter")
			caps_5.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)I420"))#,width=(int)1280,height=(int)720

			source_l = Gst.ElementFactory.make("nvv4l2camerasrc")
			source_l.set_property("device", "/dev/video{0}".format(str(self.cam.SOURCE_L)))
			source_l.set_property("do-timestamp", 1)
			
			# source_r = Gst.ElementFactory.make("nvv4l2camerasrc")
			# source_r.set_property("device", "/dev/video{0}".format(str(self.cam.SOURCE_R)))		
			# source_r.set_property("do-timestamp", 1)

			compositor = Gst.ElementFactory.make("nvcompositor")
			compositor.set_property("start-time-selection", 2)
			compositor.set_property("start-time" , 1000)

			transform = Gst.ElementFactory.make("nvegltransform")

			preview	= Gst.ElementFactory.make("nveglglessink")
			preview.set_property("sync", 0)

			conv_1 = Gst.ElementFactory.make("nvvidconv")
			# conv_2 = Gst.ElementFactory.make("nvvidconv")
			conv_3 = Gst.ElementFactory.make("nvvidconv")
			# conv_4 = Gst.ElementFactory.make("nvvidconv")
			conv_5 = Gst.ElementFactory.make("nvvidconv")
			conv_6 = Gst.ElementFactory.make("nvvidconv")

			queue_1 = Gst.ElementFactory.make("queue2")
			queue_2 = Gst.ElementFactory.make("queue2")

			# request pads from compositor
			sink_0 = compositor.get_request_pad("sink_%u")
			sink_0.set_property("xpos", 0 )
			sink_0.set_property("ypos", 0)
			sink_0.set_property("width", int(self.cap_width))
			sink_0.set_property("height", int(self.cap_height))

			# build pipeline
			self.pipeline.add(source_l)
			self.pipeline.add(caps_1)
			self.pipeline.add(conv_1)
			self.pipeline.add(caps_3)
			self.pipeline.add(conv_3)
			# self.pipeline.add(source_r)
			# self.pipeline.add(caps_2)
			# self.pipeline.add(conv_2)
			# self.pipeline.add(caps_4)
			# self.pipeline.add(conv_4)
			self.pipeline.add(compositor)
			self.pipeline.add(conv_5)
			self.pipeline.add(queue_1)
			self.pipeline.add(self.tee)
			self.pipeline.add(conv_6)
			self.pipeline.add(caps_5)
			self.pipeline.add(queue_2)
			self.pipeline.add(transform)
			self.pipeline.add(preview)

			# link pipeline elements
			source_l.link(caps_1)
			caps_1.link(conv_1)
			conv_1.link(caps_3)
			caps_3.link(conv_3)
			conv_3.link(compositor)

			# source_r.link(caps_2)
			# caps_2.link(conv_2)
			# conv_2.link(caps_4)
			# caps_4.link(conv_4)
			# conv_4.link(compositor)

			compositor.link(conv_5)
			conv_5.link(queue_1)
			queue_1.link(self.tee)
			self.tee.link(conv_6)
			conv_6.link(caps_5)
			caps_5.link(queue_2)
			queue_2.link(transform)
			transform.link(preview)

			# start pipeline
			self.pipeline.set_state(Gst.State.PLAYING)

			bus = self.pipeline.get_bus()
			bus.add_signal_watch()
			bus.enable_sync_message_emission()
			bus.connect("message", self.on_message)
			bus.connect("sync-mesage::element", self.on_sync_message)
			bus.timed_pop_filtered (Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

	def rightCamPreview(self):
		if self.pipeline is None:

			# assign selected camera
			self.cam_selected="RIGHT"

			self.pipeline = Gst.Pipeline.new("right cam preview")

			# caps_1 = Gst.ElementFactory.make("capsfilter")
			# caps_1.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)UYVY,width=(int){0},height=(int){1},framerate=(fraction){2}/1".format(str(self.cap_width), str(self.cap_height), str(self.cap_fps))))
			
			caps_2 = Gst.ElementFactory.make("capsfilter")
			caps_2.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)UYVY,width=(int){0},height=(int){1},framerate=(fraction){2}/1".format(str(self.cap_width), str(self.cap_height), str(self.cap_fps))))

			# caps_3 = Gst.ElementFactory.make("capsfilter")
			# caps_3.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)RGBA"))
			
			caps_4 = Gst.ElementFactory.make("capsfilter")
			caps_4.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)RGBA"))

			caps_5 = Gst.ElementFactory.make("capsfilter")
			caps_5.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)I420"))#,width=(int)1280,height=(int)720

			# source_l = Gst.ElementFactory.make("nvv4l2camerasrc")
			# source_l.set_property("device", "/dev/video{0}".format(str(self.cam.SOURCE_L)))
			# source_l.set_property("do-timestamp", 1)
			
			source_r = Gst.ElementFactory.make("nvv4l2camerasrc")
			source_r.set_property("device", "/dev/video{0}".format(str(self.cam.SOURCE_R)))		
			source_r.set_property("do-timestamp", 1)

			# tee_l 	= Gst.ElementFactory.make("tee")
			# tee_r 	= Gst.ElementFactory.make("tee")

			compositor = Gst.ElementFactory.make("nvcompositor")
			compositor.set_property("start-time-selection", 2)
			compositor.set_property("start-time" , 1000)

			transform = Gst.ElementFactory.make("nvegltransform")

			preview	= Gst.ElementFactory.make("nveglglessink")
			preview.set_property("sync", 0)

			# conv_1 = Gst.ElementFactory.make("nvvidconv")
			conv_2 = Gst.ElementFactory.make("nvvidconv")
			# conv_3 = Gst.ElementFactory.make("nvvidconv")
			conv_4 = Gst.ElementFactory.make("nvvidconv")
			conv_5 = Gst.ElementFactory.make("nvvidconv")
			conv_6 = Gst.ElementFactory.make("nvvidconv")

			queue_1 = Gst.ElementFactory.make("queue2")
			queue_2 = Gst.ElementFactory.make("queue2")

			# request pads from compositor
			sink_0 = compositor.get_request_pad("sink_%u")
			sink_0.set_property("xpos", 0 )
			sink_0.set_property("ypos", 0)
			sink_0.set_property("width", int(self.cap_width))
			sink_0.set_property("height", int(self.cap_height))
			
			# sink_1 = compositor.get_request_pad("sink_%u")
			# sink_1.set_property("xpos", int(self.cap_width/2))
			# sink_1.set_property("ypos", 0)
			# sink_1.set_property("width", int(self.cap_width/2))
			# sink_1.set_property("height",int(self.cap_height))


			# build pipeline
			# self.pipeline.add(source_l)
			# self.pipeline.add(tee_l)
			# self.pipeline.add(caps_1)
			# self.pipeline.add(conv_1)
			# self.pipeline.add(caps_3)
			# self.pipeline.add(conv_3)
			self.pipeline.add(source_r)
			# self.pipeline.add(tee_r)
			self.pipeline.add(caps_2)
			self.pipeline.add(conv_2)
			self.pipeline.add(caps_4)
			self.pipeline.add(conv_4)
			self.pipeline.add(compositor)
			self.pipeline.add(conv_5)
			self.pipeline.add(queue_1)
			self.pipeline.add(self.tee)
			self.pipeline.add(conv_6)
			self.pipeline.add(caps_5)
			self.pipeline.add(queue_2)
			self.pipeline.add(transform)
			self.pipeline.add(preview)

			# link pipeline elements
			# source_l.link(tee_l)			#added tee_l before caps1  
			# tee_l.link(caps_1)
			# caps_1.link(conv_1)
			# conv_1.link(caps_3)
			# caps_3.link(conv_3)
			# conv_3.link(compositor)

			source_r.link(caps_2)			#added tee_r before caps_2
			# tee_r.link(caps_2)
			caps_2.link(conv_2)
			conv_2.link(caps_4)
			caps_4.link(conv_4)
			conv_4.link(compositor)

			compositor.link(conv_5)
			conv_5.link(queue_1)
			queue_1.link(self.tee)
			self.tee.link(conv_6)
			conv_6.link(caps_5)
			caps_5.link(queue_2)
			queue_2.link(transform)
			transform.link(preview)

			# start pipeline
			self.pipeline.set_state(Gst.State.PLAYING)

			bus = self.pipeline.get_bus()
			bus.add_signal_watch()
			bus.enable_sync_message_emission()
			bus.connect("message", self.on_message)
			bus.connect("sync-mesage::element", self.on_sync_message)
			bus.timed_pop_filtered (Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

	def sideBySideCamPreview(self, isSwapped:bool=False):
		if self.pipeline is None:

			# assign selected camera
			self.cam_selected="STEREO"

			self.pipeline = Gst.Pipeline.new("side by side preview")

			caps_1 = Gst.ElementFactory.make("capsfilter")
			caps_1.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)UYVY,width=(int){0},height=(int){1},framerate=(fraction){2}/1".format(str(self.cap_width), str(self.cap_height), str(self.cap_fps))))
			
			caps_2 = Gst.ElementFactory.make("capsfilter")
			caps_2.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)UYVY,width=(int){0},height=(int){1},framerate=(fraction){2}/1".format(str(self.cap_width), str(self.cap_height), str(self.cap_fps))))

			caps_3 = Gst.ElementFactory.make("capsfilter")
			caps_3.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)RGBA"))
			
			caps_4 = Gst.ElementFactory.make("capsfilter")
			caps_4.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)RGBA"))

			caps_5 = Gst.ElementFactory.make("capsfilter")
			caps_5.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)I420")) #,width=(int)1280,height=(int)720

			source_l = Gst.ElementFactory.make("nvv4l2camerasrc")
			source_l.set_property("device", "/dev/video{0}".format(str(self.cam.SOURCE_L) if not isSwapped else str(self.cam.SOURCE_R)))
			source_l.set_property("do-timestamp", 1)
			
			source_r = Gst.ElementFactory.make("nvv4l2camerasrc")
			source_r.set_property("device", "/dev/video{0}".format(str(self.cam.SOURCE_R) if not isSwapped else str(self.cam.SOURCE_L)))		
			source_r.set_property("do-timestamp", 1)


			compositor = Gst.ElementFactory.make("nvcompositor")
			compositor.set_property("start-time-selection", 2)
			compositor.set_property("start-time" , 1000)

			transform = Gst.ElementFactory.make("nvegltransform")

			preview	= Gst.ElementFactory.make("nveglglessink")
			preview.set_property("sync", 0)

			conv_1 = Gst.ElementFactory.make("nvvidconv")
			conv_2 = Gst.ElementFactory.make("nvvidconv")
			conv_3 = Gst.ElementFactory.make("nvvidconv")
			conv_4 = Gst.ElementFactory.make("nvvidconv")
			conv_5 = Gst.ElementFactory.make("nvvidconv")
			conv_6 = Gst.ElementFactory.make("nvvidconv")

			queue_1 = Gst.ElementFactory.make("queue2")
			queue_2 = Gst.ElementFactory.make("queue2")

			# request pads from compositor
			sink_0 = compositor.get_request_pad("sink_%u")
			sink_0.set_property("xpos", 0 )
			sink_0.set_property("ypos", 0)
			sink_0.set_property("width", int(self.cap_width/2) if self.rec_4k else int(self.cap_width))
			sink_0.set_property("height", int(self.cap_height))
			
			sink_1 = compositor.get_request_pad("sink_%u")
			sink_1.set_property("xpos", int(self.cap_width/2) if self.rec_4k else int(self.cap_width))
			sink_1.set_property("ypos", 0)
			sink_1.set_property("width", int(self.cap_width/2) if self.rec_4k else int(self.cap_width))
			sink_1.set_property("height",int(self.cap_height))


			# build pipeline
			self.pipeline.add(source_l)
			# self.pipeline.add(tee_l)
			self.pipeline.add(caps_1)
			self.pipeline.add(conv_1)
			self.pipeline.add(caps_3)
			self.pipeline.add(conv_3)
			self.pipeline.add(source_r)
			# self.pipeline.add(tee_r)
			self.pipeline.add(caps_2)
			self.pipeline.add(conv_2)
			self.pipeline.add(caps_4)
			self.pipeline.add(conv_4)
			self.pipeline.add(compositor)
			self.pipeline.add(conv_5)
			self.pipeline.add(queue_1)
			self.pipeline.add(self.tee)
			self.pipeline.add(conv_6)
			self.pipeline.add(caps_5)
			self.pipeline.add(queue_2)
			self.pipeline.add(transform)
			self.pipeline.add(preview)

			# link pipeline elements
			source_l.link(caps_1)			
			caps_1.link(conv_1)
			conv_1.link(caps_3)
			caps_3.link(conv_3)
			conv_3.link(compositor)

			source_r.link(caps_2)
			caps_2.link(conv_2)
			conv_2.link(caps_4)
			caps_4.link(conv_4)
			conv_4.link(compositor)

			compositor.link(conv_5)
			conv_5.link(queue_1)
			queue_1.link(self.tee)
			self.tee.link(conv_6)
			conv_6.link(caps_5)
			caps_5.link(queue_2)
			queue_2.link(transform)
			transform.link(preview)

			# start pipeline
			self.pipeline.set_state(Gst.State.PLAYING)

			bus = self.pipeline.get_bus()
			bus.add_signal_watch()
			bus.enable_sync_message_emission()
			bus.connect("message", self.on_message)
			bus.connect("sync-mesage::element", self.on_sync_message)
			bus.timed_pop_filtered (Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
			
	def blendedCamPreview(self, isSwapped:bool=False):
		if self.pipeline is None:

			# assign selected camera
			self.cam_selected="STEREO"

			self.pipeline = Gst.Pipeline.new("blended preview")

			caps_1 = Gst.ElementFactory.make("capsfilter")
			caps_1.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)UYVY,width=(int){0},height=(int){1},framerate=(fraction){2}/1".format(str(self.cap_width), str(self.cap_height), str(self.cap_fps))))
			
			caps_2 = Gst.ElementFactory.make("capsfilter")
			caps_2.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)UYVY,width=(int){0},height=(int){1},framerate=(fraction){2}/1".format(str(self.cap_width), str(self.cap_height), str(self.cap_fps))))

			caps_3 = Gst.ElementFactory.make("capsfilter")
			caps_3.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)RGBA"))
			
			caps_4 = Gst.ElementFactory.make("capsfilter")
			caps_4.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)RGBA"))

			caps_5 = Gst.ElementFactory.make("capsfilter")
			caps_5.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)I420")) #,width=(int)1280,height=(int)720

			source_l = Gst.ElementFactory.make("nvv4l2camerasrc")
			source_l.set_property("device", "/dev/video{0}".format(str(self.cam.SOURCE_L) if not isSwapped else str(self.cam.SOURCE_R)))
			source_l.set_property("do-timestamp", 1)
			
			source_r = Gst.ElementFactory.make("nvv4l2camerasrc")
			source_r.set_property("device", "/dev/video{0}".format(str(self.cam.SOURCE_R) if not isSwapped else str(self.cam.SOURCE_L)))		
			source_r.set_property("do-timestamp", 1)


			compositor = Gst.ElementFactory.make("nvcompositor")
			compositor.set_property("start-time-selection", 2)
			compositor.set_property("start-time" , 1000)

			transform = Gst.ElementFactory.make("nvegltransform")

			preview	= Gst.ElementFactory.make("nveglglessink")
			preview.set_property("sync", 0)

			conv_1 = Gst.ElementFactory.make("nvvidconv")
			conv_2 = Gst.ElementFactory.make("nvvidconv")
			conv_3 = Gst.ElementFactory.make("nvvidconv")
			conv_4 = Gst.ElementFactory.make("nvvidconv")
			conv_5 = Gst.ElementFactory.make("nvvidconv")
			conv_6 = Gst.ElementFactory.make("nvvidconv")

			queue_1 = Gst.ElementFactory.make("queue2")
			queue_2 = Gst.ElementFactory.make("queue2")

			# request pads from compositor
			sink_0 = compositor.get_request_pad("sink_%u")
			sink_0.set_property("xpos", 0 )
			sink_0.set_property("ypos", 0)
			sink_0.set_property("width", int(self.cap_width))
			sink_0.set_property("height", int(self.cap_height))
			sink_0.set_property("alpha", (1 - self.cam_alpha))

			sink_1 = compositor.get_request_pad("sink_%u")
			sink_1.set_property("xpos", 0)
			sink_1.set_property("ypos", 0)
			sink_1.set_property("width", int(self.cap_width))
			sink_1.set_property("height", int(self.cap_height))
			sink_1.set_property("alpha", self.cam_alpha)

			# build pipeline
			self.pipeline.add(source_l)
			# self.pipeline.add(tee_l)
			self.pipeline.add(caps_1)
			self.pipeline.add(conv_1)
			self.pipeline.add(caps_3)
			self.pipeline.add(conv_3)
			self.pipeline.add(source_r)
			# self.pipeline.add(tee_r)
			self.pipeline.add(caps_2)
			self.pipeline.add(conv_2)
			self.pipeline.add(caps_4)
			self.pipeline.add(conv_4)
			self.pipeline.add(compositor)
			self.pipeline.add(conv_5)
			self.pipeline.add(queue_1)
			self.pipeline.add(self.tee)
			self.pipeline.add(conv_6)
			self.pipeline.add(caps_5)
			self.pipeline.add(queue_2)
			self.pipeline.add(transform)
			self.pipeline.add(preview)

			# link pipeline elements
			source_l.link(caps_1)			
			caps_1.link(conv_1)
			conv_1.link(caps_3)
			caps_3.link(conv_3)
			conv_3.link(compositor)

			source_r.link(caps_2)
			caps_2.link(conv_2)
			conv_2.link(caps_4)
			caps_4.link(conv_4)
			conv_4.link(compositor)

			compositor.link(conv_5)
			conv_5.link(queue_1)
			queue_1.link(self.tee)
			self.tee.link(conv_6)
			conv_6.link(caps_5)
			caps_5.link(queue_2)
			queue_2.link(transform)
			transform.link(preview)

			# start pipeline
			self.pipeline.set_state(Gst.State.PLAYING)

			bus = self.pipeline.get_bus()
			bus.add_signal_watch()
			bus.enable_sync_message_emission()
			bus.connect("message", self.on_message)
			bus.connect("sync-mesage::element", self.on_sync_message)
			bus.timed_pop_filtered (Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
			
	def calibratePreview(self):
		# 12-10-2022 LEFT/ RIGHT/ LR Previews Tested
		# blended preview temporary solution for frame alignments and zero positioning +++++++++++++++ TO BE DONE
		if self.pipeline is None:
			# assign selected camera
			self.cam_selected="STEREO"
			self.caibrator.start()


	# CREATE SECONDARY PIPELINES ******************************************************************
	def createRecordBin(self):
		# clean necessary vars
		if self.recbin is not None:
			del self.recbin
		if self.enc is not None:
			del self.enc
		if self.mux is not None:
			del self.mux
		if self.filesink is not None:
			del self.filesink

		# create record bin
		self.recbin 		= Gst.Bin.new("MASTER_BIN")

		self.enc 			= Gst.ElementFactory.make("nvv4l2h264enc")
		self.mux 			= Gst.ElementFactory.make("qtmux")
		self.filesink 		= Gst.ElementFactory.make("filesink")
		
		self.parse			= Gst.ElementFactory.make("h264parse")
		self.queue_0		= Gst.ElementFactory.make("queue2") #, "queue_0"
		self.queue_1		= Gst.ElementFactory.make("queue2") #, "queue_1"
		self.queue_2		= Gst.ElementFactory.make("queue2") #, "queue_2"
		self.convertR 		= Gst.ElementFactory.make("nvvidconv")#, "convertR"
		self.caps_video_1 	= Gst.ElementFactory.make("capsfilter")
		self.caps_video_2 	= Gst.ElementFactory.make("capsfilter")
		
		self.audiosrc		= Gst.ElementFactory.make("pulsesrc")
		self.caps_audio_1 	= Gst.ElementFactory.make("capsfilter")
		self.audioconvert 	= Gst.ElementFactory.make("audioconvert")
		self.audioresample	= Gst.ElementFactory.make("audioresample")
		self.queue_a1 		= Gst.ElementFactory.make("queue2")
		self.voenc			= Gst.ElementFactory.make("voaacenc")

		#add elements to recbin
		self.recbin.add(self.queue_0)
		self.recbin.add(self.convertR)
		self.recbin.add(self.caps_video_1)
		self.recbin.add(self.queue_1)
		self.recbin.add(self.queue_2)
		self.recbin.add(self.enc)
		self.recbin.add(self.caps_video_2)
		self.recbin.add(self.parse)
		self.recbin.add(self.mux)
		self.recbin.add(self.filesink)

		self.recbin.add(self.audiosrc)
		self.recbin.add(self.queue_a1)
		self.recbin.add(self.caps_audio_1)
		self.recbin.add(self.audioconvert)
		self.recbin.add(self.audioresample)
		self.recbin.add(self.voenc)

		#Set Properties
		current_timestamp 	= datetime.now().strftime("%Y_%m_%d-%H:%M:%S")
		file_location 		= "{1}{2}_{3}_{0}.mp4".format(str(current_timestamp), str(self.cam.DROP_LOCATION.strip()), "4K" if self.rec_4k else "HD", str(self.cam_selected)) if os.path.exists(self.cam.DROP_LOCATION.strip()) else "{1}_{2}_{0}.mp4".format(str(current_timestamp, "4K" if self.rec_4k else "HD", str(self.cam_selected)))
		self.filesink.set_property("location" , file_location)

		self.enc.set_property("qp-range", "24,24:28,28:30,30")
		self.enc.set_property("num-Ref-Frames", 2)
		self.enc.set_property("num-B-Frames", 2)
		self.enc.set_property("profile", 4)
		self.enc.set_property("maxperf-enable", True)
		self.enc.set_property("control-rate", 1)
		self.enc.set_property("bitrate", 2000000)
		self.enc.set_property("insert-aud", True)
		self.enc.set_property("insert-vui", True)

		# self.audiotestsrc.set_property("wave", "silence")
		self.voenc.set_property("bitrate", 128000)
		self.audiosrc.set_property("volume", 5)
		self.audiosrc.set_property("do-timestamp", True)
		
		self.caps_video_1.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=(string)I420, width=(int){0}, height=(int){1}".format(str(int(self.cap_width) if (self.rec_4k or self.cam_selected.strip() != "STEREO") else int(self.cap_width*2)), str(self.cap_height))))
		self.caps_video_2.set_property("caps", Gst.Caps.from_string("video/x-h264, stream-format=(string)byte-stream"))
		self.caps_audio_1.set_property("caps", Gst.Caps.from_string("audio/x-raw"))
		
		#Link recbin elements
		#Link video to mux
		self.queue_0.link(self.convertR)
		self.convertR.link(self.caps_video_1)
		self.caps_video_1.link(self.queue_1)
		self.queue_1.link(self.enc)
		self.enc.link(self.caps_video_2)
		self.caps_video_2.link(self.parse)
		self.parse.link(self.mux)

		#Link audio to mux
		self.audiosrc.link(self.caps_audio_1)
		self.caps_audio_1.link(self.queue_a1)
		self.queue_a1.link(self.audioconvert)
		self.audioconvert.link(self.audioresample)
		self.audioresample.link(self.voenc)
		self.voenc.link(self.mux)

		#Link mux to filesink
		self.mux.link(self.queue_2)
		self.queue_2.link(self.filesink)
		
		#Get pads
		self.sink_pad = self.queue_0.get_static_pad("sink")
		self.ghost_pad = Gst.GhostPad.new("sink", self.sink_pad)
		self.recbin.add_pad(self.ghost_pad)

	def createYoutubeBin(self):
		# clean necessary vars
		if self.recbin is not None:
			del self.recbin
		if self.enc is not None:
			del self.enc
		if self.mux is not None:
			del self.mux
		if self.rtmpsink is not None:
			del self.rtmpsink

		#create record bin
		self.recbin 		= Gst.Bin.new("MASTER_BIN")

		self.enc 			= Gst.ElementFactory.make("nvv4l2h264enc")
		self.mux			= Gst.ElementFactory.make("flvmux")
		self.rtmpsink		= Gst.ElementFactory.make("rtmpsink")

		self.parse			= Gst.ElementFactory.make("h264parse")
		
		self.queue_0		= Gst.ElementFactory.make("queue2")
		self.queue_1		= Gst.ElementFactory.make("queue2")
		self.queue_2		= Gst.ElementFactory.make("queue2")
		self.queue_3 		= Gst.ElementFactory.make("queue2")
		self.convertR 		= Gst.ElementFactory.make("nvvidconv")
		self.caps_video_1 	= Gst.ElementFactory.make("capsfilter")
		self.caps_video_2 	= Gst.ElementFactory.make("capsfilter")
		
		self.audiosrc		= Gst.ElementFactory.make("pulsesrc")
		self.caps_audio_1 	= Gst.ElementFactory.make("capsfilter")
		self.audioconvert 	= Gst.ElementFactory.make("audioconvert")
		self.audioresample	= Gst.ElementFactory.make("audioresample")
		self.queue_a1 		= Gst.ElementFactory.make("queue2")
		self.voenc			= Gst.ElementFactory.make("voaacenc")

		self.recbin.add(self.queue_0)
		self.recbin.add(self.convertR)
		self.recbin.add(self.caps_video_1)
		self.recbin.add(self.queue_1)
		self.recbin.add(self.enc)
		self.recbin.add(self.caps_video_2)
		self.recbin.add(self.parse)
		self.recbin.add(self.queue_2)
		self.recbin.add(self.mux)
		self.recbin.add(self.queue_3)
		self.recbin.add(self.rtmpsink)

		self.recbin.add(self.audiosrc)
		self.recbin.add(self.queue_a1)
		self.recbin.add(self.caps_audio_1)
		self.recbin.add(self.audioconvert)
		self.recbin.add(self.audioresample)
		self.recbin.add(self.voenc)

		self.enc.set_property("qp-range", "24,24:28,28:30,30")
		self.enc.set_property("maxperf-enable", 1)
		self.enc.set_property("control-rate", 1)
		self.enc.set_property("bitrate", 34000 if self.rec_4k else 6000)
		self.enc.set_property("insert-aud", 1)
		self.enc.set_property("iframeinterval", 30)
		self.enc.set_property("idrinterval", 60)

		self.mux.set_property("streamable", True)
		stream_location =  "rtmp://a.rtmp.youtube.com/live2/{0} app=live2".format(str(self.cam.YOUTUBE_STREAM_KEY.strip()))
		self.rtmpsink.set_property("location" , stream_location)

		# self.audiosrc.set_property("device", "hw:2,0")
		self.audiosrc.set_property("volume", 5)
		self.audiosrc.set_property("do-timestamp", True)
		self.voenc.set_property("bitrate", 128000)
		self.caps_video_1.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=(string)I420, width=(int){0}, height=(int){1}".format(str(int(self.cap_width) if (self.rec_4k or self.cam_selected.strip() != "STEREO") else int(self.cap_width*2)), str(self.cap_height))))
		self.caps_video_2.set_property("caps", Gst.Caps.from_string("video/x-h264, stream-format=(string)byte-stream"))
		self.caps_audio_1.set_property("caps", Gst.Caps.from_string("audio/x-raw"))
		#Link recbin elements

		#Link video to flvmux
		self.queue_0.link(self.convertR)
		self.convertR.link(self.caps_video_1)
		self.caps_video_1.link(self.queue_1)
		self.queue_1.link(self.enc)
		self.enc.link(self.caps_video_2)
		self.caps_video_2.link(self.parse)
		self.parse.link(self.queue_2)
		self.queue_2.link(self.mux)
		
		#Link audio to flvmux
		self.audiosrc.link(self.caps_audio_1)
		self.caps_audio_1.link(self.queue_a1)
		self.queue_a1.link(self.audioconvert)
		self.audioconvert.link(self.audioresample)
		self.audioresample.link(self.voenc)
		self.voenc.link(self.mux)

		#Link mux to Streaming-Sink
		self.mux.link(self.queue_3)
		self.queue_3.link(self.rtmpsink)
		
		#Get pads
		self.sink_pad = self.queue_0.get_static_pad("sink")
		self.ghost_pad = Gst.GhostPad.new("sink", self.sink_pad)
		self.recbin.add_pad(self.ghost_pad)

	def createLocalStreamBin(self):
		# clean necessary vars
		if self.recbin is not None:
			del self.recbin
		if self.enc is not None:
			del self.enc
		if self.udpsink is not None:
			del self.udpsink

		#Create elements
		self.recbin 	= Gst.Bin.new("MASTER_BIN")
		
		self.enc 		= Gst.ElementFactory.make("nvjpegenc")
		self.udpsink 	= Gst.ElementFactory.make("udpsink")
		
		self.queue_0	= Gst.ElementFactory.make("queue2")
		self.convert 	= Gst.ElementFactory.make("nvvidconv")
		self.caps_video_1 = Gst.ElementFactory.make("capsfilter")
		self.queue_1	= Gst.ElementFactory.make("queue2")
		self.rndbuffer	= Gst.ElementFactory.make("rndbuffersize")
		self.queue_2	= Gst.ElementFactory.make("queue2")

		#Set properties
		self.caps_video_1.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=(string)I420, width=(int)1280, height=(int)720"))
		self.rndbuffer.set_property("max", 65000)
		
		self.udpsink.set_property("host", "192.168.1.8")
		self.udpsink.set_property("port", 3001)
		self.udpsink.set_property("sync", 0)

		#Add elements to Bin
		self.recbin.add(self.queue_0)
		self.recbin.add(self.convert)
		self.recbin.add(self.caps_video_1)
		self.recbin.add(self.queue_1)
		self.recbin.add(self.enc)
		self.recbin.add(self.rndbuffer)
		self.recbin.add(self.queue_2)
		self.recbin.add(self.udpsink)
		
		#Link Elements
		self.queue_0.link(self.convert)
		self.convert.link(self.caps_video_1)
		self.caps_video_1.link(self.queue_1)
		self.queue_1.link(self.enc)
		self.enc.link(self.rndbuffer)
		self.rndbuffer.link(self.queue_2)
		self.queue_2.link(self.udpsink)

		#Get pads
		self.sink_pad = self.queue_0.get_static_pad("sink")
		self.ghost_pad = Gst.GhostPad.new("sink", self.sink_pad)
		self.recbin.add_pad(self.ghost_pad)


	# ATTACH SECONDARY PIPELINE TO THE PRIMARY PIPELINE *******************************************
	def initTargetBin(self, target="VR"):		
		if target == "FILE":
			self.createRecordBin()
		elif target == "YOUTUBE":
			self.createYoutubeBin()
		else:
			self.createLocalStreamBin()

	def attachMasterBin(self):
		if self.pipeline is not None:
			if self.recbin is not None:
				self.pipeline.add(self.recbin)
				self.recbin.sync_state_with_parent()
				self.tee.link(self.recbin)

		print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "secondary pipeline attached successfully", "\n")

	def startRecord(self):
		self.initTargetBin(target="FILE")
		GLib.idle_add(self.attachMasterBin)

	def startStreamYouTube(self):
		self.initTargetBin(target="YOUTUBE")
		GLib.idle_add(self.attachMasterBin)

	def startStreamLocal(self):
		self.initTargetBin(target="VR")
		GLib.idle_add(self.attachMasterBin)


	# DETTACH SECONDARY PIPELINE FROM THE PRIMARY PIPELINE ****************************************
	def dettachMasterBin(self):
		# self.recbin 	= self.pipeline.get_by_name("MASTER_BIN")
		self.ghostpad 	= self.recbin.get_static_pad("sink")
		self.teepad 	= self.ghostpad.get_peer()
		
		def blocking_pad_probe(pad, info):
			self.recbin.set_state(Gst.State.NULL)
			self.pipeline.remove(self.recbin)
			self.tee.release_request_pad(self.teepad)

			return Gst.PadProbeReturn.REMOVE

		self.teepad.add_probe(Gst.PadProbeType.BLOCK, blocking_pad_probe)

		print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "secondary pipeline dettached successfully", "\n")

	def stopRecord(self):
		if self.pipeline is not None:
			if self.enc is not None:
				self.enc.send_event(Gst.Event.new_eos())

			if self.mux is not None :
				self.mux.send_event(Gst.Event.new_eos())

			if self.rtmpsink is not None:
				self.rtmpsink.send_event(Gst.Event.new_eos())

			if self.udpsink is not None:
				self.udpsink.send_event(Gst.Event.new_eos())

			if self.filesink is not None:
				self.filesink.send_event(Gst.Event.new_eos())

			if self.recbin is not None:
				self.recbin.send_event(Gst.Event.new_eos())

		GLib.idle_add(self.dettachMasterBin)


	# CLEANUP MASTER PIPELINE *********************************************************************
	def cleanupPipeline(self):
		self.caibrator.stop()
		if self.pipeline is not None:
			self.pipeline.send_event(Gst.Event.new_eos())
			self.pipeline.set_state(Gst.State.READY)
			self.pipeline.set_state(Gst.State.NULL)
			del self.pipeline



	# GSTREAMER DEFAULT EVENT ACTIONS *************************************************************
	def on_message(self, bus, message):
		t = message.type
		# print("message type", t)
		if t == Gst.MessageType.EOS:
			print("End of Stream reached")
			self.pipeline.set_state(Gst.State.NULL)
			del self.pipeline
		elif t == Gst.MessageType.ERROR:
			err, dbg = message.parse_error()
			print("ERROR:", message.src.get_name(), ":", err.message)
			if dbg:
				print("debugging info:", dbg)
			self.pipeline.set_state(Gst.State.NULL)
			del self.pipeline
		else:
			# print("ERROR: Unexpected message received")
			pass

	def on_sync_message(self, bus, message):
		struct = message.get_structure()
		if not struct:
			return
		
		message_name = struct.get_name()
		if message_name == "prepare-xwindow-id":
			imagesink = message.src
			imagesink.set_property("force-aspect-ratio", True)
			# imagesink.set_xwindow_id("test app id")
