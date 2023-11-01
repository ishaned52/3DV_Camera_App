import os
import shutil
import subprocess

def rename_file():

    new_name = '/usr/share/backgrounds/NVIDIA_Login_Logo__.png'
    old_name = '/usr/share/backgrounds/NVIDIA_Login_Logo.png'

    # old_name = '/usr/share/backgrounds/NVIDIA_Login_Logo__.png'
    # new_name = '/usr/share/backgrounds/NVIDIA_Login_Logo.png'

    if os.path.exists(old_name):

        try:
            os.rename(old_name, new_name)
            print(f"File '{old_name}' renamed to '{new_name}' successfully.")
        except OSError as e:
            print(f"Error renaming file: {e}")

    else:
        print("file not available")

def move_file():

    source_path = 'logo.png'
    destination_path = '/usr/share/backgrounds'

    file = '/usr/share/backgrounds/NVIDIA_Login_Logo.png'

    if not os.path.exists(file):

        if os.path.exists(source_path):



            try:
                shutil.move(source_path, destination_path)
                print(f"File moved from '{source_path}' to '{destination_path}' successfully.")
            except Exception as e:
                print(f"Error moving file: {e}")

        else:
            print("image not found")

    else:
        print("file already exist")


def rename_newfile():

    old_name = '/usr/share/backgrounds/logo.png'
    new_name = '/usr/share/backgrounds/NVIDIA_Login_Logo.png'


    # old_name = '/usr/share/backgrounds/NVIDIA_Login_Logo__.png'
    # new_name = '/usr/share/backgrounds/NVIDIA_Login_Logo.png'

    if os.path.exists(old_name):

        try:
            os.rename(old_name, new_name)
            print(f"File '{old_name}' renamed to '{new_name}' successfully.")
            print("LOGO Added Successfully")
        except OSError as e:
            print(f"Error renaming file: {e}")

    else:
        print("file not available")
        


def remove_applications(self):


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


if __name__ == "__main__":

    
    rename_file()
    move_file()
    rename_newfile()
    remove_applications()



