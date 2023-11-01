import cv2
from ultralytics import YOLO

model = YOLO('yolov8n.pt')

detection_threshold =0.5

cap = cv2.VideoCapture(0)

while (True):
    ret, frame = cap.read()

    if cap == False:
        break

    results = model(frame)

    for result in results:
        detections = []
        for r in result.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = r
            x1 = int(x1)
            x2 = int(x2)
            y1 = int(y1)
            y2 = int(y2)
            class_id = int(class_id)
            if score > detection_threshold:
                detections.append([x1, y1, x2, y2, class_id])
                label = model.names[class_id]
                cv2.rectangle(frame, (x1,y1), (x2,y2), (255,0,0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    cv2.imshow('frame', frame)

    if cv2.waitKey(25) & 0xFF == ord('q'):
        cap.release()
        break

cap.release()
cv2.destroyAllWindows()