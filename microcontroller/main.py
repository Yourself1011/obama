import RPi.GPIO as GPIO
import gpiozero

pigpioFactory = gpiozero.pins.pigpio.PiGPIOFactory()
# servo = gpiozero.AngularServo(5, min_angle=0, max_angle = 180, pin_factory=pigpioFactory)
car = gpiozero.Robot(left=gpiozero.Motor(1, 2), right=gpiozero.Motor(3, 4))

while True:
    car.forward()
    sleep(2)
    car.stop()
    sleep(2)
