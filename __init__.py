from os.path import dirname
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import LOG

import RPi.GPIO as GPIO
import threading
import time
import re

__author__ = 'dony71'

# The logic of each skill is contained within its own class, which inherits
# base methods from the MycroftSkill class with the syntax you can see below:
# "class ____Skill(MycroftSkill)"
class Respeaker2MicGpioSkill(MycroftSkill):

    # The constructor of the skill, which calls Mycroft Skill's constructor
    def __init__(self):
        super(Respeaker2MicGpioSkill, self).__init__(name="Respeaker2MicGpioSkill")
        self.myKeywords = []

    # This method loads the files needed for the skill's functioning, and
    # creates and registers each intent that the skill uses
    def initialize(self):
        GPIO.setmode(GPIO.BOARD)
        Button = 11

        GPIO.setup(Button,GPIO.IN)
        GPIO.remove_event_detect(Button)
        GPIO.add_event_detect(Button,GPIO.BOTH,callback=self.ButtonHandeler)
        self.blink_active = False

        self.load_data_files(dirname(__file__))
        command_intent = IntentBuilder("GPIOIntent").\
            require("ItemKeyword").\
            optionally("ColorKeyword").\
            one_of("OnKeyword", "OffKeyword", "BlinkKeyword").build()

        self.register_intent(command_intent, self.handle_command_intent)

    def handle_command_intent(self, message):
        if "ColorKeyword" in message.data:
            if message.data["ColorKeyword"].upper() == "BLUE":
                board_pin = 32
                gpio_request = 12
                self.log.info('The pin number requested was: ' + str(board_pin))
                if "OnKeyword" in message.data:
                    self.gpio_on(board_pin, gpio_request)
                if "OffKeyword" in message.data:
                    self.gpio_off(board_pin, gpio_request)
                if "BlinkKeyword" in message.data:
                    if self.blink_active:
                        self.blink_active = False
                    else:
                        self.blink_active = True                
                        self.gpio_blink(board_pin, gpio_request)
            if message.data["ColorKeyword"].upper() == "GREEN":
                board_pin = 33
                gpio_request = 13
                self.log.info('The pin number requested was: ' + str(board_pin))
                if "OnKeyword" in message.data:
                    self.gpio_on(board_pin, gpio_request)
                if "OffKeyword" in message.data:
                    self.gpio_off(board_pin, gpio_request)
                if "BlinkKeyword" in message.data:
                    if self.blink_active:
                        self.blink_active = False
                    else:
                        self.blink_active = True
                        self.gpio_blink(board_pin, gpio_request)
        else:
            self.speak("no, l,e,d, color specified", wait=True)
            self.log.info("No LED Color Specified")

    def ButtonHandeler(self, channel):
        if GPIO.input(channel) == GPIO.HIGH:
            self.speak("button released", wait=True)
            self.log.info('Button Released')
        else:
            self.speak("button pressed", wait=True)
            self.log.info('Button Pressed')

    def gpio_on(self, board_number, gpio_request_number):
        self.blink_active = False
        GPIO.setup(board_number, GPIO.OUT, initial=0)
        self.speak_dialog("on", data={"result": str(gpio_request_number)}, wait=True)
        GPIO.output(board_number, True)
        self.log.info('Turning On GPIO Number: ' + str(gpio_request_number))

    def gpio_off(self, board_number, gpio_request_number):
        self.blink_active = False
        GPIO.setup(board_number, GPIO.OUT, initial=0)
        self.speak_dialog("off", data={"result": str(gpio_request_number)}, wait=True)
        GPIO.output(board_number, False)
        self.log.info('Turning Off GPIO Number: ' + str(gpio_request_number))

    def gpio_blink(self, board_number, gpio_request_number):
        GPIO.setup(board_number, GPIO.OUT, initial=0)
        if self.blink_active:
            self.speak("start blinking, l,e,d, timer for 10 seconds", wait=True)
            timer = threading.Timer(10, self.gpio_blink)
            timer.start()
            self.log.info('Start Blinking LED Timer for 10 seconds')

        self.speak_dialog("blink", data={"result": str(gpio_request_number)}, wait=True)
        self.log.info('Blinking GPIO Number: ' + str(gpio_request_number))

        while self.blink_active:
            if timer.is_alive():
                GPIO.output(board_number, True)
                time.sleep(0.5)
                GPIO.output(board_number, False)
                time.sleep(0.5)
            else:
                self.blink_active = False

    def stop(self):
        self.blink_active = False
        pass


# The "create_skill()" method is used to create an instance of the skill.
# Note that it's outside the class itself.
def create_skill():
    #return GPIOSkill()
    return Respeaker2MicGpioSkill()
