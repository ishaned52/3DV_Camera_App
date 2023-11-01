import cv2
import Jetson.GPIO as GPIO
import time

# GPIO pin configuration
step_pin = 11
dir_pin = 12
enable_pin = 13

# AGV control parameters
max_speed = 100  # Maximum speed of the AGV
kp = 0.5        # Proportional gain for steering control

# Initialize GPIO pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(step_pin, GPIO.OUT)
GPIO.setup(dir_pin, GPIO.OUT)
GPIO.setup(enable_pin, GPIO.OUT)
GPIO.output(enable_pin, GPIO.LOW)  # Enable the motor driver

# Set up OpenCV
cap = cv2.VideoCapture(2)  # Use appropriate camera index if needed

# Set video frame dimensions
frame_width = 640
frame_height = 480
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

# Define region of interest (ROI) for line extraction
roi_top = int(frame_height * 0.6)
roi_bottom = frame_height
roi_left = int(frame_width * 0.4)
roi_right = int(frame_width * 0.6)

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Preprocess frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)

    # Extract ROI
    roi = thresh[roi_top:roi_bottom, roi_left:roi_right]

    # Find contours in the ROI
    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Initialize line position
    line_pos = frame_width // 2

    # Process contours
    if len(contours) > 0:
        # Find the largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Calculate centroid of the largest contour
        M = cv2.moments(largest_contour)
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])

            # Update line position
            line_pos = roi_left + cx

            # Display centroid
            cv2.circle(frame, (line_pos, roi_top + cy), 5, (0, 255, 0), -1)

    # Calculate line error
    line_error = line_pos - frame_width // 2

    # Calculate steering control output
    steering_output = kp * line_error

    # Calculate AGV speeds
    left_speed = max_speed - steering_output
    right_speed = max_speed + steering_output

    # Apply speed limits
    left_speed = max(0, min(left_speed, max_speed))
    right_speed = max(0, min(right_speed, max_speed))

    # Control stepper motor
    if line_error > 0:
        GPIO.output(dir_pin, GPIO.HIGH)  # Set direction
    else:
        GPIO.output(dir_pin, GPIO.LOW)  # Set direction

    # Step the motor
    steps = abs(line_error)  # Adjust the number of steps as needed
    for _ in range(steps):
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(0.001)  # Adjust the delay as needed for motor speed
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(0.001)  # Adjust the delay as needed for motor speed

    # Display line and steering info
    cv2.line(frame, (frame_width // 2, roi_top), (line_pos, roi_bottom), (0, 0, 255), 2)
    cv2.putText(frame, f"Line Error: {line_error}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Display frame
    cv2.imshow("Line Follower", frame)

    # Exit if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
GPIO.output(enable_pin, GPIO.HIGH)  # Disable the motor driver
GPIO.cleanup()
cap.release()
cv2.destroyAllWindows()