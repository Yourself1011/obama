import gpiozero
from gpiozero.pins.lgpio import LGPIOFactory
from time import sleep

lgpioFactory = LGPIOFactory()
mouthServo = gpiozero.AngularServo(27, min_angle=0, max_angle = 180, pin_factory=lgpioFactory)
car = gpiozero.Robot(left=gpiozero.Motor(3, 2), right=gpiozero.Motor(17, 4))

while True:
    # car.forward()
    servo.angle = 0
    sleep(2)
    # car.stop()
    servo.angle = 180
    sleep(2)
