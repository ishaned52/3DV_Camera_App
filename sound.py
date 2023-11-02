import subprocess

def list_usb_audio_input_devices():
    try:
        output = subprocess.check_output(['arecord', '-l'], stderr=subprocess.STDOUT, universal_newlines=True)
        lines = output.split('\n')
        
        usb_device_count = 0
        usb_device_names = []
        
        for line in lines:
            if "USB Audio Device" in line:
                usb_device_count += 1
                device_name = line.strip().split(":")[-1].strip()
                usb_device_names.append(device_name)
        
        print(f"Total USB audio input devices detected: {usb_device_count}")
        print("List of available USB audio input device names:")
        for name in usb_device_names:
            print(name)
    except subprocess.CalledProcessError as e:
        print("Error:", e.output)

if __name__ == "__main__":
    list_usb_audio_input_devices()
