#!/bin/bash
NODE=/sys/class/pwm/pwmchip1
CHANNEL="$1"
PERIOD="$2"
DUTY_CYCLE="$3"

function usage {
	printf "Usage: $0 <channel> <period> <duty_cycle>\n"
	printf "    channel - number from 0-3\n"
	printf "    period - PWM period in nanoseconds\n"
	printf "    duty_cycle - Duty Cycle (on period) in nanoseconds\n"
	exit 1
}

if [[ ! $CHANNEL =~ ^[0-3]+$ ]]; then
	usage
fi

if [ -d "$NODE/device/consumer:platform:cooling_fan/" ]; then
	echo "Hold your horses, looks like this is pwm1?"
	exit 1
fi

if [ ! -d "$NODE/pwm$CHANNEL" ]; then
	echo "0" | sudo tee -a "$NODE/export"
fi

echo "0" | sudo tee -a "$NODE/pwm$CHANNEL/enable" > /dev/null
echo "$PERIOD" | sudo tee -a "$NODE/pwm$CHANNEL/period" > /dev/null
if [ $? -ne 0 ]; then
	echo "^ don't worry, handling it!"
	echo "$DUTY_CYCLE" | sudo tee -a "$NODE/pwm$CHANNEL/duty_cycle" > /dev/null
	echo "$PERIOD" | sudo tee -a "$NODE/pwm$CHANNEL/period" > /dev/null
else
	echo "$DUTY_CYCLE" | sudo tee -a "$NODE/pwm$CHANNEL/duty_cycle" > /dev/null
fi
echo "1" | sudo tee -a "$NODE/pwm$CHANNEL/enable" > /dev/null


case $CHANNEL in
	"0")
	PIN="12"
	FUNC="a0"
	;;
	"1")
	PIN="13"
	FUNC="a0"
	;;
	"2")
	PIN="18"
	FUNC="a3"
	;;
	"3")
	PIN="19"
	FUNC="a3"
esac

# Sure, the pin is set to the correct alt mode by the dtoverlay at startup...
# But we'll do this to protect the user (me, the user is me) from themselves:
pinctrl set $PIN $FUNC

echo "PWM$CHANNEL set to $PERIOD ns, $DUTY_CYCLE, on pin $PIN (func $FUNC)."
