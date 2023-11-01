import subprocess

# Deactivate the F1 key and get the output of the command
output = subprocess.run(['xmodmap', '-e', 'keycode 133 = '], capture_output=True)

# Print the output of the command
print(output.stdout)
