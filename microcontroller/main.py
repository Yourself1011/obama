import RPi.GPIO as GPIO
import gpiozero

pigpioFactory = gpiozero.pins.pigpio.PiGPIOFactory()
servo = gpiozero.AngularServo(3, min_angle=0, max_angle = 180, pin_factory=pigpioFactory)

while True:
    servo.angle = 10
    sleep(1)
    servo.angle = 20
    sleep(1)
