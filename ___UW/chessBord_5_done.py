import cv2
import pandas as pd
import numpy as np

CB_Size = (8, 6)

capL = cv2.VideoCapture(0)
capR = cv2.VideoCapture(1)

while (True):
    retL, frameL = capL.read()
    retR, frameR = capR.read()

    if retL == True and retR == True:
        retvalL, cornersL = cv2.findChessboardCorners(frameL, patternSize= CB_Size)
        retvalR, cornersR = cv2.findChessboardCorners(frameR, patternSize= CB_Size)

        if retvalL and retvalR:
            frameL = cv2.drawChessboardCorners(frameL, CB_Size, cornersL, retvalL)
            frameR = cv2.drawChessboardCorners(frameR, CB_Size, cornersR, retvalR)

            cornersL = np.squeeze(cornersL)
            cornersR = np.squeeze(cornersR)
            left     = pd.DataFrame(cornersL)
            right    = pd.DataFrame(cornersR)

            difference_list = left.subtract(right)
            difference_list = difference_list.astype(int)

            mod = difference_list.mode()
            difference = mod.median()

            print("Median of column: ", difference)

            cv2.putText(frameL, str(difference[0]), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.putText(frameR, str(difference[1]), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

            print('********************************************')

        combine = cv2.hconcat([frameL, frameR])

        cv2.imshow('frame combine', combine)

    if cv2.waitKey(25) & 0xFF == ord('q'):
        capL.release()
        break

capL.release()
cv2.destroyAllWindows()