
import gpiozero
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

pigpioFactory = PiGPIOFactory()
mouthServo = gpiozero.AngularServo(27, min_angle=0, max_angle = 180, pin_factory=pigpioFactory)

mult = 10
i = 0 * (1 / mult)
while True:
    mouthServo.angle = i * mult
    print(i * mult)
    sleep(2)
    i += 1
