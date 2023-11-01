
class Select3DPreview(base_21, form_21):

    def __init__(self, pipeline):
        super(base_21, self).__init__()
        self.setupUi(self)
        self.pipeline = pipeline
        self.sys = System()
        self.resizeWindow()

        print("3333")

        self.closeButton.clicked.connect(self.closeEvent)
        self.buttonStart.clicked.connect(self.buttonStartClickAction)
        self.buttonStart.clicked.connect(self.closeEvent)

        
    def buttonStartClickAction(self):

        index = self.comboBoxSelectPreviewType.currentIndex()

        if index == 0:

            self.pipeline.stop_preview()
            sleep(2)
            self.pipeline.blendCameraPreview()

            pass

        elif index ==1:

            self.pipeline.stop_preview()
            sleep(2)
            self.pipeline.sideByside()

            pass
        elif index == 2:

            pass

    def closeEvent(self, event):
        self.close()


    def resizeWindow(self):

        self.x = self.sys.SELECT_3D_PREVIEW_WINDOW_X
        self.y = self.sys.SELECT_3D_PREVIEW_WINDOW_Y

        self.resize(int(self.x), int(self.y))
        pass

    def resizeEvent(self, event):

        size = self.size()
        self.x = size.width()
        self.y = size.height()
        self.sys.SELECT_3D_PREVIEW_WINDOW_X = self.x
        self.sys.SELECT_3D_PREVIEW_WINDOW_Y = self.y
        self.sys.save()

