import cv2

class Calibrator():
    def __init__(self) -> None:
        self.capL=None
        self.capR=None

    def start(self):
        self.capL = cv2.VideoCapture()
        self.capR = cv2.VideoCapture()

        self.capL.open(0, cv2.CAP_V4L2)
        self.capR.open(1, cv2.CAP_V4L2)

        self.capL.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capL.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.capR.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capR.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        if not self.capL.isOpened():
            self.stop()
        if not self.capR.isOpened():
            self.stop()

        while (True):
            retL, frameL = self.capL.read()
            retR, frameR = self.capR.read()

            if retL==True and retR==True:
                left_frame_gray     = cv2.cvtColor(frameL, cv2.COLOR_BGR2GRAY)
                right_frame_gray    = cv2.cvtColor(frameR, cv2.COLOR_BGR2GRAY)

                frame_diff = cv2.absdiff(left_frame_gray, right_frame_gray)

                cv2.imshow('CALIBRATE', frame_diff)

                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    break
            else:
                break

        self.stop()

    def stop(self):
        cv2.destroyAllWindows()
        
        if self.capL is not None:
            self.capL.release()
        if self.capR is not None:
            self.capR.release()
        
        self.capL=None
        self.capR=None        