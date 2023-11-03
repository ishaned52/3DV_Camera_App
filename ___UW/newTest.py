import subprocess

source_name = 'alsa_input.usb-GeneralPlus_USB_Audio_Device-00.mono-fallback'

# Run the pactl command and capture its output
command = f"pactl list sources | grep -A 10 'Name: {source_name}' | grep 'Volume:' | awk -F/ '{{print $2}}' | awk '{{print $1}}' | head -n 1"
output = subprocess.check_output(command, shell=True, text=True)

# Extract the first volume percentage
volume_percentage = output.strip().replace('%', '')

print(f"Volume percentage for source '{source_name}': {volume_percentage}")
