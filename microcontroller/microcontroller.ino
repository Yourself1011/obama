#include <IBusBM.h>

#define ENA 18
#define ENB 19

IBusBM IBus;

void setup() {
    Serial.begin(115200);
    IBus.begin(Serial2, 1);  // iBUS object connected to serial2 RX2 pin using timer 1
    // myservo.attach(servoPin);  // attaches the servo on pin 18 to the servo object (using timer 0)

    pinMode(14, OUTPUT);
    pinMode(27, OUTPUT);
    pinMode(26, OUTPUT);
    pinMode(25, OUTPUT);

    ledcSetup(0, 5000, 10);
    ledcAttachPin(ENA, 0);
    ledcSetup(1, 5000, 10);
    ledcAttachPin(ENB, 1);
}

enum DirectionState {
    FORWARD,
    BACKWARD,
    LEFT,
    RIGHT,
    STOP,
};

struct State {
    DirectionState direction;
    int xSpeed;
    int ySpeed;
};

State currentState = {STOP, 0, 0};

void applyState() {
    switch (currentState.direction) {
        case STOP:
            digitalWrite(14, LOW);
            digitalWrite(27, LOW);
            digitalWrite(26, LOW);
            digitalWrite(25, LOW);
            break;
        case FORWARD:
            digitalWrite(14, LOW);
            digitalWrite(27, HIGH);
            digitalWrite(26, LOW);
            digitalWrite(25, HIGH);
            break;
        case BACKWARD:
            digitalWrite(14, HIGH);
            digitalWrite(27, LOW);
            digitalWrite(26, HIGH);
            digitalWrite(25, LOW);

            break;
    }

    ledcWrite(0, map(currentState.xSpeed, 0, 1000, 0, 1023));
    ledcWrite(1, map(currentState.ySpeed, 0, 1000, 0, 1023));
}

void loop() {
    int xVal = IBus.readChannel(0);
    int yVal = IBus.readChannel(1);

    // Failsafe for lost signal
    if (xVal == 0 || yVal == 0) {
        currentState.direction = STOP;
        currentState.xSpeed = 0;
        currentState.ySpeed = 0;
        applyState();
        delay(20);
        return;
    }

    const int deadband = 50;
    int throttle = 0;  // 0..1000 magnitude
    int steer = 0;     // 0..1000 magnitude
    bool steerRight = false;

    // Determine direction and throttle magnitude
    if (yVal > 1500 + deadband) {
        currentState.direction = FORWARD;
        throttle = (yVal - 1500 - deadband) * 2;
    } else if (yVal < 1500 - deadband) {
        currentState.direction = BACKWARD;
        throttle = (1500 - deadband - yVal) * 2;
    } else {
        currentState.direction = STOP;
        throttle = 0;
    }
    if (throttle > 1000) throttle = 1000;

    // Determine steering magnitude and side
    if (xVal > 1500 + deadband) {
        steerRight = true;
        steer = (xVal - 1500 - deadband) * 2;
    } else if (xVal < 1500 - deadband) {
        steerRight = false;
        steer = (1500 - deadband - xVal) * 2;
    } else {
        steer = 0;
    }
    if (steer > 1000) steer = 1000;

    int leftSpeed = 0;   // ENA
    int rightSpeed = 0;  // ENB

    if (throttle == 0 && steer == 0) {
        currentState.direction = STOP;
        leftSpeed = 0;
        rightSpeed = 0;
    } else if (throttle > 0 && steer == 0) {
        // Straight: both full throttle
        leftSpeed = throttle;
        rightSpeed = throttle;
    } else if (throttle > 0 && steer > 0) {
        // Curving: reduce inner wheel proportionally to steering
        if (steerRight) {
            leftSpeed = throttle;
            rightSpeed = throttle - steer;
        } else {
            leftSpeed = throttle - steer;
            rightSpeed = throttle;
        }
        if (leftSpeed < 0) leftSpeed = 0;
        if (rightSpeed < 0) rightSpeed = 0;
    } else {
        // No throttle but steering input: stop (no pivot)
        currentState.direction = STOP;
        leftSpeed = 0;
        rightSpeed = 0;
    }

    currentState.xSpeed = leftSpeed;
    currentState.ySpeed = rightSpeed;

    applyState();

    delay(20);
}
