source_l = f"{self.source_1} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv "
        source_r = f"{self.source_2} sensor-mode={sensor_mode} ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, format=(string)NV12, framerate=(fraction){fps}/1  ! nvvidconv "
