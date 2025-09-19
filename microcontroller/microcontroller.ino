#define ENA 18
#define ENB 19

// Simple iBUS protocol variables
uint16_t ibusChannels[10];
bool ibusConnected = false;

// Keyboard control variables
bool keyboardMode = true;
unsigned long lastKeyboardCommand = 0;
const unsigned long KEYBOARD_TIMEOUT = 500; // 500ms timeout for keyboard commands

void setup() {
    Serial.begin(115200);
    Serial2.begin(115200);  // iBUS serial connection
    // myservo.attach(servoPin);  // attaches the servo on pin 18 to the servo object (using timer 0)

    pinMode(14, OUTPUT);
    pinMode(27, OUTPUT);
    pinMode(26, OUTPUT);
    pinMode(25, OUTPUT);

    ledcAttach(ENA, 5000, 10);
    ledcAttach(ENB, 5000, 10);
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
State keyboardState = {STOP, 0, 0};

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

    ledcWrite(ENA, map(currentState.xSpeed, 0, 1000, 0, 1023));
    ledcWrite(ENB, map(currentState.ySpeed, 0, 1000, 0, 1023));
}

// Simple iBUS protocol reader
bool readIBus() {
    static uint8_t ibusBuffer[32];
    static uint8_t ibusIndex = 0;
    static unsigned long lastIBusTime = 0;
    
    // Reset if too much time has passed
    if (millis() - lastIBusTime > 100) {
        ibusIndex = 0;
    }
    
    while (Serial2.available()) {
        uint8_t val = Serial2.read();
        lastIBusTime = millis();
        
        // Look for iBUS header (0x20 0x40)
        if (ibusIndex == 0 && val != 0x20) continue;
        if (ibusIndex == 1 && val != 0x40) {
            ibusIndex = 0;
            continue;
        }
        
        ibusBuffer[ibusIndex] = val;
        ibusIndex++;
        
        // Complete packet received (32 bytes)
        if (ibusIndex >= 32) {
            // Simple checksum validation
            uint16_t checksum = 0xFFFF;
            for (int i = 0; i < 30; i++) {
                checksum -= ibusBuffer[i];
            }
            
            uint16_t receivedChecksum = (ibusBuffer[31] << 8) | ibusBuffer[30];
            
            if (checksum == receivedChecksum) {
                // Extract channel data
                for (int i = 0; i < 10; i++) {
                    int pos = 2 + i * 2;
                    ibusChannels[i] = (ibusBuffer[pos + 1] << 8) | ibusBuffer[pos];
                }
                ibusConnected = true;
                ibusIndex = 0;
                return true;
            }
            ibusIndex = 0;
        }
    }
    
    // Check for timeout
    if (millis() - lastIBusTime > 200) {
        ibusConnected = false;
    }
    
    return false;
}

void processKeyboardCommand() {
    if (Serial.available() > 0) {
        char command = Serial.read();
        lastKeyboardCommand = millis();
        keyboardMode = true;
        
        switch (command) {
            case 'w':
            case 'W':
                keyboardState.direction = FORWARD;
                keyboardState.xSpeed = 800;  // Full speed
                keyboardState.ySpeed = 800;
                break;
            case 's':
            case 'S':
                keyboardState.direction = BACKWARD;
                keyboardState.xSpeed = 800;
                keyboardState.ySpeed = 800;
                break;
            case 'a':
            case 'A':
                keyboardState.direction = FORWARD;
                keyboardState.xSpeed = 400;  // Left wheel slower
                keyboardState.ySpeed = 800;  // Right wheel faster
                break;
            case 'd':
            case 'D':
                keyboardState.direction = FORWARD;
                keyboardState.xSpeed = 800;  // Left wheel faster
                keyboardState.ySpeed = 400;  // Right wheel slower
                break;
            case ' ':  // Spacebar for stop
            case 'x':
            case 'X':
                keyboardState.direction = STOP;
                keyboardState.xSpeed = 0;
                keyboardState.ySpeed = 0;
                break;
        }
    }
    
    // Check for keyboard timeout
    if (keyboardMode && (millis() - lastKeyboardCommand > KEYBOARD_TIMEOUT)) {
        keyboardMode = false;
        keyboardState.direction = STOP;
        keyboardState.xSpeed = 0;
        keyboardState.ySpeed = 0;
    }
}

void loop() {
    // Process keyboard commands first
    processKeyboardCommand();
    
    // If in keyboard mode, use keyboard state
    if (keyboardMode) {
        currentState = keyboardState;
        applyState();
        delay(20);
        return;
    }
    
    // Otherwise, use iBUS control
    readIBus();
    
    // Failsafe for lost signal
    if (!ibusConnected || ibusChannels[0] == 0 || ibusChannels[1] == 0) {
        currentState.direction = STOP;
        currentState.xSpeed = 0;
        currentState.ySpeed = 0;
        applyState();
        delay(20);
        return;
    }
    
    int xVal = ibusChannels[0];
    int yVal = ibusChannels[1];

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
