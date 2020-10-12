# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import time
import logging
import virtualbox
from core.exceptions import BoxNotFoundError, BoxNotRunningError, BoxAlreadyRunningError
from virtualbox.library import VBoxErrorObjectNotFound, OleErrorUnexpected

logger = logging.getLogger(__name__)

KEYBOARD_KEYS = ['ESC', '1', '!', '2', '@', '3', '#', '4', '$', '5', '%', '6', '^', '7', '&', '8', '*',
                 '9', '(', '0', ')', '-', '_', '=', '+', 'BKSP', '\x08', 'TAB', '\t', 'q', 'Q', 'w', 'W',
                 'e', 'E', 'r', 'R', 't', 'T', 'y', 'Y', 'u', 'U', 'i', 'I', 'o', 'O', 'p', 'P', '[', '{',
                 ']', '}', 'ENTER', '\r', '\n', 'CTRL', 'a', 'A', 's', 'S', 'd', 'D', 'f', 'F', 'g', 'G',
                 'h', 'H', 'j', 'J', 'k', 'K', 'l', 'L', ';', ':', "'", '"', '`', '~', 'LSHIFT', '\\', '|',
                 'z', 'Z', 'x', 'X', 'c', 'C', 'v', 'V', 'b', 'B', 'n', 'N', 'm', 'M', ',', '<', '.', '>',
                 '/', '?', 'RSHIFT', 'PRTSC', 'ALT', 'SPACE', ' ', 'CAPS', 'F1', 'F2', 'F3', 'F4', 'F5',
                 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'NUM', 'SCRL', 'HOME', 'UP', 'PGUP', 'MINUS',
                 'LEFT', 'CENTER', 'RIGHT', 'PLUS', 'END', 'DOWN', 'PGDN', 'INS', 'DEL', 'E_DIV', 'E_ENTER',
                 'E_INS', 'E_DEL', 'E_HOME', 'E_END', 'E_PGUP', 'E_PGDN', 'E_LEFT', 'E_RIGHT', 'E_UP',
                 'E_DOWN', 'RALT', 'RCTRL', 'LWIN', 'RWIN', 'PAUSE']
MODIFIERS = ['CTRL', 'SHIFT', 'LSHIFT', 'RSHIFT', 'ALT', 'RALT', 'RCTRL', 'LWIN', 'RWIN', 'WIN']


class VirtualBoxSrv():
    def __init__(self, name, delay):
        self.default_delay = delay
        self.delay = None
        self.expiration_time = None
        self.vbox = virtualbox.VirtualBox()
        self.session = virtualbox.Session()
        try:
            self.machine = self.vbox.find_machine(name)
        except VBoxErrorObjectNotFound:
            self.machine = None
            raise BoxNotFoundError

    def __str__(self):
        if self.machine:
            return f"{self.machine.name} on VirtualBox"
        return "VirtualBox machine not initialized"

    def _sanitize_text(self, text):
        text = text.replace('€', '')
        text = text.replace('¡', '')
        return text

    def get_special_keys(self):
        return ' | '.join([x for x in KEYBOARD_KEYS if len(x) > 1])

    def set_delay(self, delay, expiration=None):
        self.expiration_time = None
        self.delay = delay
        if expiration:
            self.expiration_time = int(time.time()) + expiration
        logger.info("Press delay is now %sms, expires in %ssec", self.delay, expiration)

    def get_delay(self):
        if self.delay is not None:
            if not self.expiration_time or (self.expiration_time and self.expiration_time > int(time.time())):
                logger.debug("Returning changed delay %s", self.delay)
                return self.delay
            logger.debug("Resetting delay to default: %s", self.default_delay)
            self.delay = self.default_delay
        logger.debug("Returning default delay %s", self.default_delay)
        return self.default_delay

    def is_running(self):
        if self.machine is None:
            return False
        return int(self.machine.state) == 5

    def cleanup(self):
        if self.session is None:
            return
        try:
            self.shut_down(True)
        except BoxNotRunningError:
            pass
        try:
            self.session.unlock_machine()
        except OleErrorUnexpected:
            pass

    def launch(self):
        if self.is_running():
            raise BoxAlreadyRunningError
        if not self.is_running() and self.machine:
            progress = self.machine.launch_vm_process(self.session, "gui", "")
            progress.wait_for_completion()

    def restore(self):
        snapshot = self.session.machine.current_snapshot
        progress = self.session.machine.restore_snapshot(snapshot)
        progress.wait_for_completion()

    def shut_down(self, save, restore=False):
        if not self.is_running():
            raise BoxNotRunningError
        if save:
            progress = self.session.machine.save_state()
        else:
            progress = self.session.console.power_down()
        progress.wait_for_completion()
        if restore:
            self.restore()

    def snapshot(self, username):
        progress, _ = self.session.machine.take_snapshot(f"{int(time.time())}", f"Taken by {username}", True)
        progress.wait_for_completion()

    def type(self, text):
        if not self.is_running():
            raise BoxNotRunningError
        if type(text) is not str:
            raise TypeError
        text = self._sanitize_text(text)
        logger.debug("Typing '%s'", text)
        try:
            self.session.console.keyboard.put_keys(text, press_delay=self.get_delay())
        except Exception as e:
            logger.exception(e)

    def send(self, keys):
        if not self.is_running():
            raise BoxNotRunningError
        to_press = []
        to_hold = set()
        for key in keys:
            if len(key) > 1:
                key = key.upper()
            if key in MODIFIERS:
                if key in ['WIN', 'SHIFT']:
                    key = 'L' + key
                to_hold.add(key)
            elif key in KEYBOARD_KEYS:
                to_press.append(key)
            else:
                pass
        if not to_press and not to_hold:
            logger.debug("No keys to press")
            return []
        self.session.console.keyboard.put_keys(press_keys=to_press, hold_keys=list(to_hold))
        logger.debug("Holding keys %s while pressing %s", to_hold, to_press)
        return list(to_hold) + to_press

    def release(self):
        if not self.is_running():
            raise BoxNotRunningError
        self.session.console.keyboard.release_keys()
