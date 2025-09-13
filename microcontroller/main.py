import RPi.GPIO as GPIO
import gpiozero

lgpioFactory = gpiozero.pins.lgpio.LGPIOFactory()
# servo = gpiozero.AngularServo(5, min_angle=0, max_angle = 180, pin_factory=lgpioFactory)
car = gpiozero.Robot(left=gpiozero.Motor(2, 3), right=gpiozero.Motor(4, 17))

while True:
    car.forward()
    sleep(2)
    car.stop()
    sleep(2)
