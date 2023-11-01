import os
import subprocess

def open_app(directory, app_name):
    # open a new terminal window
    subprocess.Popen(['gnome-terminal'])

    # change the directory in the terminal
    cd_command = 'cd "{}"'.format(directory)
    app_command = './{}'.format(app_name)
    full_command = '{} && {}'.format(cd_command, app_command)

    subprocess.Popen(['gnome-terminal', '-x', 'bash', '-c', full_command])

# example usage
open_app('/home/giocam3d/3DV', './app')


