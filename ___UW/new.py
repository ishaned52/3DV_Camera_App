import cv2

# Load the image
image = cv2.imread("ui/New folder/background_4k.png")  # Replace with the actual file path

if image is not None:
    # Check the shape of the image
    height, width, channels = image.shape

    if channels == 3:
        if image[0, 0, 0] == image[0, 0, 2]:
            print("The image is in RGB format (Red, Green, Blue).")
        elif image[0, 0, 0] == image[0, 0, 1]:
            print("The image is in BGR format (Blue, Green, Red).")
        else:
            print("The image has 3 channels but the order is not clear.")
    else:
        print("The image does not have 3 channels, so its format cannot be determined.")
else:
    print("Failed to read the image.")
