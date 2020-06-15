# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# All credits go to domcross (Github https://github.com/domcross)

import time
from mycroft.messagebus.message import Message
from mycroft.skills.core import intent_handler
from adapt.intent import IntentBuilder
from mycroft.util.log import LOG
from mycroft import intent_file_handler
from .pixels import Pixels

from os.path import dirname, abspath
import sys
import requests
import json
import threading

sys.path.append(abspath(dirname(__file__)))

from adapt.intent import IntentBuilder
try:
    from mycroft.skills.core import MycroftSkill
except:
    class MycroftSkill:
        pass

import GPIO


class Respeaker2MicLedSkill(MycroftSkill):

    def on_gpio12_change(self):
        """used to report the state of the led.
        This is attached to the on change event.  And will speak the
        status of the led.
        """
        status = GPIO.get("GPIO12")
        self.speak("Led is %s" % status)

    def on_gpio13_change(self):
        status = GPIO.get("GPIO13")
        self.speak("Led is %s" % status)

    def on_button_change(self):
        status = GPIO.get("Button")
        self.speak("Button is %s" % status)

    def __init__(self):
        self.blink_active = False
        GPIO.on("GPIO12",self.on_gpio12_change)
        GPIO.on("GPIO13",self.on_gpio13_change)
        GPIO.on("Button",self.on_button_change)
        super(Respeaker2MicLedSkill, self).__init__(name="Respeaker2MicLedSkill")

    def blink_gpio12(self):
        """This Will Start the Led blink process
        This function will start the led blink process and continue
        until blink_active is false.
        """
        if self.blink_active:
            threading.Timer(10, self.blink_gpio12).start()
        if self.blink_active:
            if GPIO.get("GPIO12")!="On":
                GPIO.set("GPIO12","On")
            else:
                GPIO.set("GPIO12","Off")

    def blink_gpio13(self):
        if self.blink_active:
            threading.Timer(10, self.blink_gpio13).start()
        if self.blink_active:
            if GPIO.get("GPIO13")!="On":
                GPIO.set("GPIO13","On")
            else:
                GPIO.set("GPIO13","Off")

    def initialize(self):
        self.pixels = Pixels()
        self.log.info("Pixel Ring: Initializing")
        self.enable()
        self.pixels.wakeup()
        self.pixels.off()
        """This function will initialize the Skill for Blinking an LED
        This creates two intents
            * IoCommandIntent - Will fire for any command that controlls the LED
            * SystemQueryIntent - Will fire for any system command
        The SystemQueryIntent was desinged for debug info while testing
        and is not required going forward.
        """
        self.load_data_files(dirname(__file__))
        command_intent = IntentBuilder("IoCommandIntent").require("command").require("ioobject").optionally("ioparam").build()
        system_intent = IntentBuilder("SystemQueryIntent").require("question").require("systemobject").build()
        self.register_intent(command_intent, self.handle_command_intent)
        self.register_intent(system_intent, self.handle_system_intent)

    def enable(self):
        self.log.info("Pixel Ring: Enabling")
       	self.add_event('recognizer_loop:wakeword',
                        self.handle_listener_wakeup)
        self.add_event('recognizer_loop:record_begin',
                        self.handle_listener_listen)
        self.add_event('recognizer_loop:record_end',
                        self.handle_listener_off)
        self.add_event('mycroft.skill.handler.start',
                        self.handle_listener_think)
        self.add_event('mycroft.skill.handler.complete',
                        self.handle_listener_off)
        self.add_event('recognizer_loop:audio_output_start',
                        self.handler_listener_speak)
        self.add_event('recognizer_loop:audio_output_end',
                        self.handle_listener_off)

    def disable(self):
        self.log.info("Pixel Ring: Disabling")
        self.remove_event('recognizer_loop:wakeup')
        self.remove_event('recognizer_loop:record_begin')
        self.remove_event('recognizer_loop:record_end')
        self.remove_event('recognizer_loop:audio_output_start')
        self.remove_event('recognizer_loop:audio_output_end')
        self.remove_event('mycroft.skill.handler.start')
        self.remove_event('mycroft.skill.handler.complete')

    def handle_listener_wakeup(self, message):
        self.log.info("Pixel Ring: Wakeup")
        self.pixels.wakeup()
        time.sleep(3)

    def handle_listener_listen(self, message):
        self.log.info("Pixel Ring: Listen")
        self.pixels.listen()
        time.sleep(3)

    def handle_listener_think(self, message):
        self.log.info("Pixel Ring: Think")
        self.pixels.think()
        time.sleep(3)

    def handler_listener_speak(self, message):
        self.log.info("Pixel Ring: Speak")
        self.pixels.speak()
        time.sleep(3)

    def handle_listener_off(self, message):
        self.log.info("Pixel Ring: Off")
        self.pixels.off()
        time.sleep(3)

    @intent_handler(IntentBuilder("").require("EnablePixelRing"))
    def handle_enable_pixel_ring_intent(self, message):
        self.enable()
        self.speak_dialog("EnablePixelRing")

    @intent_handler(IntentBuilder("").require("DisablePixelRing"))
    def handle_disable_pixel_ring_intent(self, message):
        self.disable()
        self.speak_dialog("DisablePixelRing")

    def handle_system_intent(self, message):
        """This is the handeler for system intent.
        This will handle all questions of the system for debug info.
        Args:
            message(obj):
                This is the object containing the message that fired the
                intent.  This is used to discover what to do within the
                intent.
        """
        if message.data["systemobject"] == "Name":
            self.speak_dialog("name")
            self.speak(__name__)
        elif message.data["systemobject"] == "GPIO":
            self.speak_dialog("check")
            if GPIO.is_imported:
                self.speak("GPIO is Imported")
            else:
                self.speak("GPIO is not Imported")
        elif message.data["systemobject"] == "Modules":
            self.speak_dialog("modules")
            for module in sys.modules:
                self.speak(module)
        elif message.data["systemobject"] == "Path":
            self.speak_dialog("path")
            for path in sys.path:
                self.speak(path)

    def handle_command_intent(self, message):
        """This will handle all command intents for controlling GPIO
        This handles all commands to controll the LEDS including checking
        the status.
        Args:
            message(obj):
                This is the object containing the message that fired the
                intent.  This is used to discover what to do within the
                intent.
        """
        if message.data["command"].upper() == "BLINKING":
            #if message.data["ioobject"].upper() == "RED LED":
            if message.data["ioobject"].upper() == "BLUE LED":
                #self.speak_dialog("redledblink")
                self.speak_dialog("blueledblink")
                if self.blink_active:
                    self.blink_active = False
                else:
                    self.blink_active = True
                    self.blink_gpio12()
            elif message.data["ioobject"].upper() == "GREEN LED":
                self.speak_dialog("greenledblink")
                if self.blink_active:
                    self.blink_active = False
                else:
                    self.blink_active = True
                    self.blink_gpio13()
            elif message.data["ioparam"].upper() == "STOP":
                self.stop()
        elif message.data["command"].upper() == "STATUS":
            #if message.data["ioobject"].upper() == "RED LED":
            if message.data["ioobject"].upper() == "BLUE LED":
                self.on_gpio12_change()
            elif message.data["ioobject"].upper() == "GREEN LED":
                self.on_gpio13_change()
        elif message.data["command"].upper() == "TURN":
            #if message.data["ioobject"].upper() == "RED LED":
            if message.data["ioobject"].upper() == "BLUE LED":
                if "ioparam" in message.data:
                    if message.data["ioparam"].upper() == "ON":
                        self.blink_active = False
                        GPIO.set("GPIO12","On")
                    elif message.data["ioparam"].upper() == "OFF":
                        self.blink_active = False
                        GPIO.set("GPIO12","Off")
                else:
                    self.speak_dialog("ipparamrequired")
            elif message.data["ioobject"].upper() == "GREEN LED":
                if "ioparam" in message.data:
                    if message.data["ioparam"].upper() == "ON":
                        self.blink_active = False
                        GPIO.set("GPIO13","On")
                    elif message.data["ioparam"].upper() == "OFF":
                        self.blink_active = False
                        GPIO.set("GPIO13","Off")
                else:
                    self.speak_dialog("ipparamrequired")

    def stop(self):
        """This function will clean up the Skill"""
        self.speak("Stop Blinking, L,E,D", wait = True)
        self.blink_active = False

def create_skill():
    return Respeaker2MicLedSkill()
