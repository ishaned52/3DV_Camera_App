import subprocess
import os

# Check if the script is being run as root
if os.geteuid() != 0:
    print("Please run this script as root.")
    exit(1)

# Define a list of packages to remove
packages_to_remove = [
    "gnome-calculator",
    "libreoffice*",
    "cheese",
    "simple-scan",
    "aisleriot",
    "thunderbird",
    "gnome-mines",
    "shotwell",
    "gnome-sudoku",
    "rhythmbox",
    "gnome-mahjongg",
    "gnome-todo",
    "transmission-common",
    "xterm",
]

# Construct the apt remove command
apt_remove_command = ["apt", "remove", "--purge"] + packages_to_remove

# Execute the command
try:
    subprocess.check_call(apt_remove_command)
    print("Packages removed successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
    exit(1)
