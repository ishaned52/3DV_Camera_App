from simple_pid import PID

# Initialize the PID controller with specific gains
pid = PID(Kp=0.5, Ki=0.2, Kd=0.1)

# Set the desired setpoint
setpoint = 10.0

# Control loop
while True:
    # Measure the process variable
    process_variable = measure_process_variable()

    # Compute the error
    error = setpoint - process_variable

    # Compute the control output
    control_output = pid(error)

    # Apply the control output to regulate the process variable
    regulate_process_variable(control_output)
