import subprocess

def mount_external_drive(drive_path, mount_point):
    try:
        subprocess.check_output(['sudo', 'mount', drive_path, mount_point])
        print(f"Drive {drive_path} mounted at {mount_point}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

def unmount_external_drive(mount_point):
    try:
        subprocess.check_output(['sudo', 'umount', mount_point])
        print(f"Drive at {mount_point} unmounted")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

# Replace these paths with your SSD drive path and desired mount point
drive_path = '/dev/nvme0n1p1'  # Replace X with the appropriate drive identifier (e.g., 'a', 'b', 'c', etc.)
mount_point = '/media/nvidia/GIOVIEW2'  # Replace with your desired mount point

# Mount the drive
mount_external_drive(drive_path, mount_point)

# Unmount the drive
unmount_external_drive(mount_point)
