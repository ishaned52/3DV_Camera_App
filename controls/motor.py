from controls.settings import Motor, MotorPresets, System, AISettings
import serial


class MotorParameters():
    conf = Motor()
    mp=MotorPresets()
    sys = System()
    # ai = AISettings()

    # INIT MOTOR PARAMS
    def __init__(self):
        self.load_params()

    # LOAD STORED PARAMETERS FROM FILES
    def load_params(self) -> bool:
                    #speed, power
        self.M1 = self.conf.M1
        self.M2 = self.conf.M2
        self.M3 = self.conf.M3
        self.M4 = self.conf.M4
        self.M5 = self.conf.M5
        self.M6 = self.conf.M6
        self.M7 = self.conf.M7
        
        return True

    # READ PARAMETRS OF ONE MOTOR
    def read_params(self, motor:int):
        # RETURN POWER, SPEED
        if motor==1 :  return self.M1[0], self.M1[1]
        elif motor==2 :return self.M2[0], self.M2[1]
        elif motor==3 :return self.M3[0], self.M3[1]
        elif motor==4 :return self.M4[0], self.M4[1]
        elif motor==5 :return self.M5[0], self.M5[1]
        elif motor==6 :return self.M6[0], self.M6[1]
        elif motor==7 :return self.M7[0], self.M7[1]
        else : return 0,0

    # SAVE SPEED TO CONFIG FILE
    def update_speed(self, m1:int, m2:int=0, speed:int=0) -> bool:
        if m1==1 :  self.conf.M1[0]=speed
        elif m1==2 :self.conf.M2[0]=speed
        elif m1==3 :self.conf.M3[0]=speed
        elif m1==4 :self.conf.M4[0]=speed
        elif m1==5 :self.conf.M5[0]=speed
        elif m1==6 :self.conf.M6[0]=speed
        elif m1==7 :self.conf.M7[0]=speed
        else : pass

        if m2==1 :  self.conf.M1[0]=speed
        elif m2==2 :self.conf.M2[0]=speed
        elif m2==3 :self.conf.M3[0]=speed
        elif m2==4 :self.conf.M4[0]=speed
        elif m2==5 :self.conf.M5[0]=speed
        elif m2==6 :self.conf.M6[0]=speed
        elif m2==7 :self.conf.M7[0]=speed
        else : pass
        
        self.conf.save()
        return True

    # SAVE POWER TO CONFIG FILE
    def update_power(self, m1:int, m2:int=0, power:int=0) -> bool:
        if m1==1 :  self.conf.M1[1]=power
        elif m1==2 :self.conf.M2[1]=power
        elif m1==3 :self.conf.M3[1]=power
        elif m1==4 :self.conf.M4[1]=power
        elif m1==5 :self.conf.M5[1]=power
        elif m1==6 :self.conf.M6[1]=power
        elif m1==7 :self.conf.M7[1]=power
        else : pass

        if m2==1 :  self.conf.M1[1]=power
        elif m2==2 :self.conf.M2[1]=power
        elif m2==3 :self.conf.M3[1]=power
        elif m2==4 :self.conf.M4[1]=power
        elif m2==5 :self.conf.M5[1]=power
        elif m2==6 :self.conf.M6[1]=power
        elif m2==7 :self.conf.M7[1]=power
        else : pass
        
        self.conf.save()
        return True

    # MOTOR MOVE STEPS
    def move_steps(self, m1:int, m2:int=0, move:bool=False, direction:int=0, steps:int=0):
        
        cmd = bytearray()

        #get first motor speed and power
        spd, pw = self.read_params(motor=m1)

        cmd1_a,_ = self.__SetMotorPowerSpeed(motor=m1, power=pw, speed=spd)

        # modified 18-04-2023
        # on Kumuditha's request to adjust the home position correction
        
        # if(m2 == 4): # change the direction
        #         direction = 1 if direction == 0 else 0

        if(m1 == 5 or m1== 6): # change the direction
            direction = 1 if direction == 0 else 0

        cmd1_b,_ = self.__SetMotorDirection(motor=m1, direction=direction)
        
        cmd1_c,_ = self.__SetMotorSteps(motor=m1, steps=steps)
        cmd1_d,_ = self.__SetMotorMoveStop(motor=m1, move=move)

        print("motor 1 dir : ", direction)
        
        cmd.extend(cmd1_a)
        cmd.extend(cmd1_b)
        cmd.extend(cmd1_c)
        cmd.extend(cmd1_d)

        if m2 != 0:
            #get second motor speed and power
            spd, pw = self.read_params(motor=m2)

            cmd2_a,_ = self.__SetMotorPowerSpeed(motor=m2, power=pw, speed=spd)

            # modified 18-04-2023
            # on Kumuditha's request to adjust the home position correction

            # if(m2 == 4): # change the direction
            #     direction = 1 if direction == 0 else 0

            #Seperation (1,6), Convergance  (2,5), Tilt (3,4)
            # if m2==6:          
            #     direction=1 if self.conf.SEC_MTR_INVERSE_SEPERATION else 0

            # if m2==5:
            #     direction=1 if self.conf.SEC_MTR_INVERSE_CONVERGENCE else 0

            # if m2==4:
            #     direction=1 if self.conf.SEC_MTR_INVERSE_TILT else 0

            if(m2 == 5 or m2== 6): # change the direction
                direction = 1 if direction == 0 else 0

            cmd2_b,_ = self.__SetMotorDirection(motor=m2, direction=1 if direction == 0 else 0)
            cmd2_c,_ = self.__SetMotorSteps(motor=m2, steps=steps)
            cmd2_d,_ = self.__SetMotorMoveStop(motor=m2, move=move)

            print("motor 2 dir : ", direction)

            cmd.extend(cmd2_a)
            cmd.extend(cmd2_b)
            cmd.extend(cmd2_c)
            cmd.extend(cmd2_d)
        
        return cmd
        
    # MOTOR MOVE HOME
    def move_home(self, m1:int, m2:int=0):
        
        cmd = bytearray()

        #get first motor speed and power
        spd, pw = self.read_params(m1)
        cmd_a,_ = self.__SendMotorHome(motor=m1, speed=spd)

        cmd.extend(cmd_a)

        if m2 != 0:
            #get second motor speed and power
            spd, pw = self.read_params(m2)
            cmd_b,_ = self.__SendMotorHome(motor=m2, speed=spd)

            cmd.extend(cmd_b)

        #return motor, power
        return cmd

    # STOP MOVING MOTORS
    def move_stop(self, m1:int, m2:int=0):
        cmd = bytearray()

        cmd1_a,_ = self.__SetMotorMoveStop(motor=m1)
        cmd.extend(cmd1_a)

        if m2 != 0:
            cmd2_a,_ = self.__SetMotorMoveStop(motor=m2)
            cmd.extend(cmd2_a)
        
        return cmd





	# CMD BUILDING PRIVATE METHODS LIST 
    def __SetMotorPowerSpeed(self, motor, power, speed):
        # build control command
        cmd = bytearray(6)

        cmd[0] = int('01', 16)  # id
        cmd[1] = int('03', 16)  # length
        cmd[2] = motor          # 1 - 7
        cmd[3] = power          # 0 - 255
        cmd[4] = speed          # 0 - 255

        # check sum calculation
        cksm = cmd[0] + cmd[1] + cmd[2] + cmd[3] + cmd[4]
        cksm = cksm &255

        cmd[5] = cksm

        # expected response length
        response_buffer_size = 6

        return cmd, response_buffer_size
    
    def __SetMotorDirection(self, motor, direction):
        # build control command
        cmd = bytearray(5)

        cmd[0] = int('02', 16)  # id
        cmd[1] = int('02', 16)  # length
        cmd[2] = motor          # 1 - 7
        cmd[3] = direction      # 1 > cw  |  0 > ccw

        # check sum calculation
        cksm = cmd[0] + cmd[1] + cmd[2] + cmd[3]
        cksm = cksm &255

        cmd[4] = cksm

        # expected response length
        response_buffer_size = 6

        return cmd, response_buffer_size
    
    def __SetMotorSteps(seld, motor, steps):
        # build control command
        cmd = bytearray(7)

        cmd[0] = int('03', 16)  # id
        cmd[1] = int('04', 16)  # length
        cmd[2] = motor          # 1 - 7

        # 3 bytes steps value convert in to an array
        # stps = steps.to_bytes(3, 'big')     # big endian
        stps = steps.to_bytes(3, 'little')  # little endian

        cmd[3] = stps[2]        # 
        cmd[4] = stps[1]        # 
        cmd[5] = stps[0]        # 

        # check sum calculation
        cksm = cmd[0] + cmd[1] + cmd[2] + cmd[3] + cmd[4] + cmd[5]
        cksm = cksm &255

        cmd[6] = cksm

        # expected response length
        response_buffer_size = 6

        return cmd, response_buffer_size
    
    def __SetMotorMoveStop(self, motor, move:bool=False):
        # build control command
        cmd = bytearray(5)

        cmd[0] = int('04', 16)  # id
        cmd[1] = int('02', 16)  # length
        cmd[2] = motor          # 1 - 7
        cmd[3] = int('01', 16) if move == True else int('00', 16) # 01 move 00 stop

        # check sum calculation
        cksm = cmd[0] + cmd[1] + cmd[2] + cmd[3]
        cksm = cksm &255

        cmd[4] = cksm

        # expected response length
        response_buffer_size = 6

        return cmd, response_buffer_size

    def __SendMotorHome(self, motor, speed):
        # build control command
        cmd = bytearray(5)

        cmd[0] = int('05', 16)  # id
        cmd[1] = int('02', 16)  # length
        cmd[2] = motor          # 1 - 7
        cmd[3] = speed          # 0 - 255

        # check sum calculation
        cksm = cmd[0] + cmd[1] + cmd[2] + cmd[3]
        cksm = cksm &255

        cmd[4] = cksm

        # expected response length
        response_buffer_size = 6

        return cmd, response_buffer_size


    def __MotorPositionRequest(self, motor):
        # build control command
        cmd = bytearray(4)

        cmd[0] = int('07', 16)  # id
        cmd[1] = int('01', 16)  # length
        cmd[2] = motor          # 1 - 7

        # check sum calculation
        cksm = cmd[0] + cmd[1] + cmd[2]
        cksm = cksm &255

        cmd[3] = cksm

        # expected response length
        response_buffer_size = 6

        return cmd, response_buffer_size

    def __MotorSwitchStatusGet(self, motor):
        # build control command
        cmd = bytearray(4)

        cmd[0] = int('08', 16)  # id
        cmd[1] = int('01', 16)  # length
        cmd[2] = motor          # 1 - 7

        # check sum calculation
        cksm = cmd[0] + cmd[1] + cmd[2]
        cksm = cksm &255

        cmd[3] = cksm

        # expected response length
        response_buffer_size = 6

        return cmd, response_buffer_size

    def __LightBrightnessControl(self, light_id, brightness):

        # build control command
        cmd = bytearray(6)

        cmd[0] = int('09', 16)  # id
        cmd[1] = int('03', 16)  # length
        cmd[2] = light_id       # 1 - 7

        # 2 bytes brightness value convert in to an array
        brgt = brightness.to_bytes(2, 'big')     # big endian
        # brgt = brightness.to_bytes(2, 'little')  # little endian
        
        cmd[3] = brgt[1]
        cmd[4] = brgt[0]

        # check sum calculation
        cksm = cmd[0] + cmd[1] + cmd[2] + cmd[3] + cmd[4]
        cksm = cksm &255

        cmd[5] = cksm

        # expected response length
        response_buffer_size = 6

        return cmd, response_buffer_size




    def move_preset(self, preset_num):
        # s,p = self.motors.read_params(self.control_motor_left)
        cmd = bytearray()

        for motor_num in range(1,7):

            try:
                stp=int(self.mp.presets["P{}".format(preset_num)]["M{}".format(motor_num)]["STEPS"])
                dir=int(self.mp.presets["P{}".format(preset_num)]["M{}".format(motor_num)]["DIRECTION"])
                cmd.extend(self.move_steps(m1=motor_num, move=True, direction=dir, steps=stp))

            except:
                pass

        self.sendSerialCommand(cmd=cmd)
        

    def move_end(self):

        cmd = bytearray()

        for motor_num in range(1,7):
            cmd.extend(self.move_stop(m1=motor_num))

        self.sendSerialCommand(cmd=cmd)

    
    def preset_name(self, preset_num):
        name = None

        try:
            
            name = str(self.mp.presets["P{}".format(preset_num)]["NAME"])

        except:
            pass

        return name

    def preset_availability(self, preset_num):
        availability=False
        name = None
        try:
            
            str(self.mp.presets["P{}".format(preset_num)])
            availability = True
            name = str(self.mp.presets["P{}".format(preset_num)]["NAME"])
            print("fff")
        except:
            pass
            

        return availability , name

        


    def sendSerialCommand(self,cmd):

        print("send >>> ", ''.join('{:02x}'.format(x) for x in cmd))
        with serial.Serial(self.sys.PORT, self.sys.BAUD_RATE, timeout=2) as ser:
            ser.write(cmd)
            # print(cmd)










