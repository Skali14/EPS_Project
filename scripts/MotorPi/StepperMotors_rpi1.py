import threading

from DRV8825_rpi1 import DRV8825

class Motors:
    def __init__(self):
        self.Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))
        self.Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4, mode_pins=(21, 22, 27))

    def run_motor1(self, direction, step_count) -> None:
        print("motor1 starting")
        self.Motor1.SetMicroStep('softward', 'fullstep')
        self.Motor1.TurnStep(Dir=direction, steps=step_count, stepdelay=0.000001)
        print("motor1 finished")
        self.Motor1.Stop()

    def run_motor2(self, direction, step_count) -> None:
        print("motor2 starting")
        self.Motor2.SetMicroStep('softward', 'fullstep')
        self.Motor2.TurnStep(Dir=direction, steps=step_count, stepdelay=0.000001)
        print("motor2 finished")
        self.Motor2.Stop()

    def run_both_motors_forward(self, step_count) -> None:
        motor1_thread = threading.Thread(target=self.run_motor1, args=('forward', step_count))
        motor2_thread = threading.Thread(target=self.run_motor2, args=('forward', step_count))

        motor1_thread.start()
        motor2_thread.start()

        motor1_thread.join()
        motor2_thread.join()

    def run_both_motors_backward(self, step_count) -> None:
        motor1_thread = threading.Thread(target=self.run_motor1, args=('backward', step_count))
        motor2_thread = threading.Thread(target=self.run_motor2, args=('backward', step_count))

        motor1_thread.start()
        motor2_thread.start()

        motor1_thread.join()
        motor2_thread.join()