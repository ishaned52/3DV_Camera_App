import subprocess

# Define the source name you want to check
source_name = 'alsa_input.usb-GeneralPlus_USB_Audio_Device-00.mono-fallback'

# Run the pactl command and capture its output
output = subprocess.check_output(['pactl', 'list', 'sources'], text=True)

# Split the output into lines
lines = output.splitlines()

# Initialize a variable to store the mute status
mute_status = None

# Iterate through the lines to find the mute status
for i, line in enumerate(lines):
    if source_name in line:
        for j in range(i, len(lines)):
            if 'Mute:' in lines[j]:
                mute_status = lines[j].split()[-1]
                break
        break

# Check and display the mute status
if mute_status is not None:
    if mute_status == 'yes':
        print(f"{source_name} is muted.")
    elif mute_status == 'no':
        print(f"{source_name} is unmuted.")
else:
    print(f"{source_name} was not found.")
