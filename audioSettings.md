pactl set-source-volume alsa_input.usb-GeneralPlus_USB_Audio_Device-00.mono-fallback 90%



mute

pactl set-source-mute alsa_input.usb-GeneralPlus_USB_Audio_Device-00.mono-fallback 0


pactl set-default-source alsa_input.usb-GeneralPlus_USB_Audio_Device-00.mono-fallback


arecord -l


pactl list short sources

pactl list sources | grep -A 10 'Name: alsa_input.platform-sound.analog-stereo' | grep 'Mute:'



current volume

pactl list sources | grep 'Name: alsa_input.usb-GeneralPlus_USB_Audio_Device-00.mono-fallback' -A 10 | grep 'Volume:' | awk -F/ '{print $2}' | awk '{print $1}'
