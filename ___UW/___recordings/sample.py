
    def caliculatePID(self, diff):

        error = diff
        # print("difference", diff)
        control_motor = 5

        if self.cam.SOURCE_L==0 and self.cam.SOURCE_R==1:
            pos_direction = 1
            neg_direction = 0

        if self.cam.SOURCE_L==1 and self.cam.SOURCE_R==0:
            pos_direction = 0
            neg_direction = 1

        Kp=0.2
        Ki=0.2
        Kd=0.1

        delta_error = error - self.previous_error

        pValue = Kp * error
        iValue = Ki * (delta_error)
        dValue = Kd * self.total_error
        
        pidValue = pValue + iValue+ dValue
        pidValue = abs(int(pidValue))
        print("pidValue", pidValue)
        self.previous_error = error
        self.total_error = self.total_error + error
        nu_of_steps = pidValue

        print("nu-of-steps", nu_of_steps)

        if self.correction_checker==True:

            if diff < 0:

                cmd = self.motors.move_steps(m1=control_motor, move=True, direction=pos_direction, steps=nu_of_steps)
                self.motors.sendSerialCommand(cmd=cmd)
                pass
            elif diff>0:

                cmd = self.motors.move_steps(m1=control_motor, move=True, direction=neg_direction, steps=nu_of_steps)
                self.motors.sendSerialCommand(cmd=cmd)
            else:
                pass
            
        pass

