
import gpiozero
from gpiozero.pins.lgpio import LGPIOFactory
from time import sleep

lgpioFactory = LGPIOFactory()
mouthServo = gpiozero.AngularServo(27, min_angle=0, max_angle = 180, pin_factory=lgpioFactory, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)
car = gpiozero.Robot(left=gpiozero.Motor(3, 2), right=gpiozero.Motor(17, 4))

mult = 0.5
i = 108 * (1 / mult)
while True:
    mouthServo.angle = i * mult
    print(i * mult)
    sleep(2)
    i -= 1
