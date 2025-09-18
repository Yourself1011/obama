
import gpiozero
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

pigpioFactory = PiGPIOFactory()
mouthServo = gpiozero.AngularServo(27, min_angle=0, max_angle = 180, pin_factory=pigpioFactory)
armServo1 = gpiozero.AngularServo(14, min_angle=0, max_angle = 180, pin_factory=pigpioFactory)
armServo2 = gpiozero.AngularServo(15, min_angle=0, max_angle = 180, pin_factory=pigpioFactory)
armServo1.angle = 0
armServo2.angle = 180

mult = 10
i = 100 * (1 / mult)
while True:
    print(i * mult)
    mouthServo.angle = i * mult
    sleep(2)
    i += 1
