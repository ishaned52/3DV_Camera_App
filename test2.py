import subprocess

# Run the pactl command and capture its output
output = subprocess.check_output(["pactl", "list", "short", "sources"], text=True)

# Split the output into lines
lines = output.splitlines()

# Extract device names and store them in a list
device_names = [line.split('\t')[1] for line in lines]

# Print the device names
for device_name in device_names:
    print(device_name)
