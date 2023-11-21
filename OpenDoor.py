"""
from assembly import slot
def OpenDoor():
	print("OpenDoor")
	slot(True)
"""

def opendoor():
    import RPi.GPIO as GPIO
    import time
    GPIO.setmode(GPIO.BOARD)
    BUTTON_GPIO = 11  # You can use a different GPIO pin
    LOCK_GPIO = 8
    GPIO.setup(LOCK_GPIO, GPIO.OUT)
    state = False
    print("slot functie gaat runnen met state: ", state)
    if not state:
        print("slot gaat open")
        GPIO.output(LOCK_GPIO, GPIO.HIGH)
        time.sleep(5)
        print("slot gaat toe")
        GPIO.output(LOCK_GPIO, GPIO.LOW)
    elif state:
        print(f"slot gaat toe: {state} (elif satement) ")
        GPIO.output(LOCK_GPIO, GPIO.LOW)
