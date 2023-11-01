import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
from skimage.metrics import structural_similarity

model = YOLO('yolov8n.pt')
detection_threshold = 0.5
crop_height = 400
crop_width  = 400

def crop_image(frame, frame_width, frame_height, crop_width, crop_height):
    x_start = int((frame_width/2)  - (crop_width/2))
    x_end   = int((frame_width/2)  + (crop_width/2))
    y_start = int((frame_height/2) - (crop_height/2))
    y_end   = int((frame_height/2) + (crop_height/2))

    cv2.rectangle(frame, (x_start, y_start), (x_end, y_end), (255, 255, 0), 2)
    crop = frame [y_start : y_end, x_start : x_end]

    return crop, x_start, y_start

def object_detection(frame, results, x, y):
    for result in results:
        detections = []
        for r in result.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = r
            x1 = int(x1) + x
            y1 = int(y1) + y
            x2 = int(x2) + x
            y2 = int(y2) + y
            class_id = int(class_id)    # 0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench', 14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat', 35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich', 49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza', 54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave', 69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'
            if class_id == 0 or class_id == 65 or class_id == 67:   # 0: 'person', 65: 'remote', 67: 'cell phone'
                if score > detection_threshold:
                    label = model.names[class_id]
                    detections.append([x1, y1, x2, y2, class_id, label])
    return frame, detections
    
def orb_sim__(frameL, frameR):
    orb = cv2.ORB_create()
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    kpL, dpL = orb.detectAndCompute(frameL, None)
    kpR, dpR = orb.detectAndCompute(frameR, None)

    matches = bf.match(dpL, dpR)
    matches = sorted(matches, key=lambda x: x.distance)

    similar_regions = [i for i in matches if i.distance <50]

    img_matches = cv2.drawMatches(frameL, kpL, frameR, kpR, matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    
    if len(matches) > 0:
        return len(similar_regions) / len(matches), img_matches
    
    else:
        return 0.0, img_matches 
    

def orb_sim(frameL, frameR):
    orb = cv2.ORB_create()
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    kpL, dpL = orb.detectAndCompute(frameL, None)
    kpR, dpR = orb.detectAndCompute(frameR, None)

    if dpL is None or dpR is None:
        return 0.0, None

    matches = bf.match(dpL, dpR)
    matches = sorted(matches, key=lambda x: x.distance)

    similar_regions = [i for i in matches if i.distance < 50]

    img_matches = cv2.drawMatches(frameL, kpL, frameR, kpR, matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    if len(matches) > 0:
        return len(similar_regions) / len(matches), img_matches
    else:
        return 0.0, img_matches


def structural_sim(frameL, frameR):
    sim, diff = structural_similarity(frameL, frameR, full=True)
    return sim

def hog_sim(frameL, frameR):
    hog = cv2.HOGDescriptor()
    
    featuresL = hog.compute(frameL)
    featuresR = hog.compute(frameR)

    featuresL /= np.linalg.norm(featuresL)
    featuresR /= np.linalg.norm(featuresR)

    similarity = np.dot(featuresL.T, featuresR)

    return similarity


capL = cv2.VideoCapture(0)
capR = cv2.VideoCapture(1)

while (True):
    retL, frameL = capL.read()
    retR, frameR = capR.read()

    if retL == False and retR == False:
        break

    frame_height, frame_width, _ = frameL.shape

    cropL, x_start, y_start = crop_image(frameL, frame_width, frame_height, crop_width, crop_height)
    cropR, x_start, y_start = crop_image(frameR, frame_width, frame_height, crop_width, crop_height)

    resultsL = model(cropL)
    resultsR = model(cropR)

    Draw_frameL, detectionsL = object_detection(frameL.copy(), resultsL, x_start, y_start)
    Draw_frameR, detectionsR = object_detection(frameR.copy(), resultsR, x_start, y_start)

    for l in detectionsL:
        for r in detectionsR:
            x1_L, x1_R = l[0], r[0]
            y1_L, y1_R = l[1], r[1]
            x2_L, x2_R = l[2], r[2]
            y2_L, y2_R = l[3], r[3]
            id_L, id_R = l[4], r[4]
            name = l[5]

            if id_L == id_R:
                objectL = cv2.cvtColor((frameL [y1_L : y2_L, x1_L : x2_L]), cv2.COLOR_BGR2GRAY)
                objectR = cv2.cvtColor((frameR [y1_R : y2_R, x1_R : x2_R]), cv2.COLOR_BGR2GRAY)

                HL, WL = objectL.shape
                HR, WR = objectR.shape

                if ((WL - WR) > -4 or (WL - WR) < 4):
                    orb_similarity, combine = orb_sim(objectL, objectR)
                    print('Similarity using ORB is : ', orb_similarity)

                    resizeL = cv2.resize(objectL, (crop_width, crop_height))
                    resizeR = cv2.resize(objectR, (crop_width, crop_height))

                    ssim_similarity = structural_sim(resizeL, resizeR)
                    print('Similarity using SSIM is : ', ssim_similarity)

                    hog_similarity = hog_sim(resizeL, resizeL)
                    print("Similarity using HOG is : ", hog_similarity)

                    if orb_similarity > 0.8:
                        cv2.imshow('frame combine', combine)

                        cv2.rectangle(Draw_frameL, (x1_L, y1_L), (x2_L, y2_L), (255, 0, 0), 2)
                        cv2.rectangle(Draw_frameR, (x1_R, y1_R), (x2_R, y2_R), (255, 0, 0), 2)

                        cx_L, cy_L = (x1_L + x2_L) // 2 , (y1_L + y2_L) // 2
                        cx_R, cy_R = (x1_R + x2_R) // 2 , (y1_R + y2_R) // 2
                        cv2.circle(Draw_frameL, (cx_L, cy_L), 5, (0, 0, 255), -1)
                        cv2.circle(Draw_frameR, (cx_R, cy_R), 5, (0, 0, 255), -1)

                        x1_diff = abs(int(x1_L - x1_R))
                        x2_diff = abs(int(x2_L - x2_R))
                        cx_diff = abs(int(cx_L - cx_R))

                        x_difference = [x1_diff, x2_diff, cx_diff]

                        print('x_difference', x_difference)
                        # def reject_outliers(data, m=1):
                        #     return data[abs(data - np.mean(data)) < m * np.std(data)]
                    
                        dfx = pd.Series(np.array(x_difference))
                        mod	= dfx.mode()
                        difference = mod.median()
                        print('mod difference', difference)

                        cv2.putText(Draw_frameL, str(difference), (x_start, y_start - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow('frame draw left', Draw_frameL)
    cv2.imshow('frame draw Right', Draw_frameR)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        capL.release()
        capR.release()
        break

capL.release()
capR.release()
cv2.destroyAllWindows()