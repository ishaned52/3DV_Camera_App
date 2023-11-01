# default db9 port connected to /dev/ttyTHS0 on Floyd NX
# ls -l /dev/ttyTHS0
# sudo chmod o+rw /dev/ttyTHS0
# stty 9600 -F /dev/ttyTHS0
# stty 9600 < /dev/ttyTHS0
# cat -v < /dev/ttyTHS0
# echo -ne "TESTING SERIAL PORT IS WORKING FINE" > /dev/ttyTHS0
# echo -ne "HEX STRING \x7E\x03\xD0\xAF AND\n NORMAL TEXT \r\n" > /dev/ttyUSB0

# sudo chmod o+rw /dev/ttyUSB0
# echo -e "\x0C\x08\x01\xA0\xFD\x00\x00\xC8\x01\x01\x7C\r" > /dev/ttyUSB0
# echo -e "\x0C\x08\x01\xA0\xFD\x00\x00\xC8\x00\x01\x7B\r" > /dev/ttyUSB0
# echo -e "\x0C\x08\x01\xA0\xFD\x00\x00\xC8\x01\x01\x7C\r" > /dev/ttyUSB0
# echo -e "\x03\x04\x01\x00\x00\x01\x09\x02\x02\x01\x01\x06\x04\x02\x01\x01\x08\r" > /dev/ttyUSB0

'''
MOTOR1
01 03 01 A0 FF A4  	-Motor 1 speed 255
01 03 01 00 FE 03  	-Motor 1 speed 254
01 03 01 00 FD 02  	-Motor 1 speed 253
01 03 01 00 FC 01  	-Motor 1 speed 252
01 03 01 00 FB 00  	-Motor 1 speed 251
01 03 01 00 FA FF  	-Motor 1 speed 250
01 03 01 00 C8 CD  	-Motor 1 speed 200
01 03 01 00 64 69  	-Motor 1 speed 100
01 03 01 00 0A 0F  	-Motor 1 speed 10
01 03 01 00 01 06  	-Motor 1 speed 1


02 02 01 00 05		- Motor1 direction acw.
02 02 01 01 06		- Motor1 direction cw.

03 04 01 00 05 C8 D5	- Motor1 steps 5*256+200
03 04 01 00 00 1A 22	- Motor1 steps 26
03 04 01 00 00 03 0B	- Motor1 steps 3
03 04 01 00 00 02 0A	- Motor1 steps 2
03 04 01 00 00 01 09	- Motor1 steps 1
03 04 01 00 00 C8 D0	- Motor1 steps 200


04 02 01 01 08		- Motor1 start.
04 02 01 00 07		- Motor1 stop.




08 01 01 0A		-Motor switch status request.
07 01 01 09		-Motor position request.

05 02 01 A0 A8		-Motor move home command.
0E 04 01 01 02 03 19 	-Motor set positon command


0C 08 01 A0 FD 00 00 C8 00 01 7B   /200 step/200 spd/ cw
0C 08 01 A0 FD 00 00 C8 01 01 7C   /200 step/200 spd/ acw

03 04 01 00 00 01 09 02 02 01 00 05 04 02 01 01 08 /1stp-acw
03 04 01 00 00 01 09 02 02 01 01 06 04 02 01 01 08 /1stp-cw

03 04 01 00 00 02 0A 02 02 01 00 05 04 02 01 01 08 /2stp-acw
03 04 01 00 00 02 0A 02 02 01 01 06 04 02 01 01 08 /2stp-cw

03 04 01 00 00 03 0B 02 02 01 00 05 04 02 01 01 08 /3stp-acw
03 04 01 00 00 03 0B 02 02 01 01 06 04 02 01 01 08 /3stp-cw

03 04 01 00 00 1A 22 02 02 01 00 05 04 02 01 01 08 /26stp-acw
03 04 01 00 00 1A 22 02 02 01 01 06 04 02 01 01 08 /26stp-cw

03 04 01 00 00 C8 D0 02 02 01 00 05 04 02 01 01 08 /200stp-acw
03 04 01 00 00 C8 D0 02 02 01 01 06 04 02 01 01 08 /200stp-cw

Light Brightness
09 03 08 00 02 16
'''
