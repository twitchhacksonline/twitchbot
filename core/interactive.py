# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import cmd
import logging
from core.objects.flag import FLAG_CAPTURED_SUCCESSFULLY
from core.exceptions import ProfileNotFoundError, BoxAlreadyRunningError, BoxNotRunningError,\
    ChallengeNotFoundError, DuplicateFlagError, FlagNotFoundError, NoChallengeSelectedError

logger = logging.getLogger(__name__)


def _optional_value(question):
    result = input("(optional) " + question)
    if not result:
        return None
    else:
        return result


def _demand_integer(question):
    result = None
    while result is None:
        try:
            result = int(input(question))
            return result
        except ValueError:
            print("  Please provide an integer value")


class Interactive(cmd.Cmd):
    intro = 'Twitch Hacks Online. Interactive Console'
    prompt = '> '

    def __init__(self, state):
        self.state = state
        super().__init__()

    def preloop(self):
        if self.state.profile:
            cmd.sys.stdout.write("Loaded default:")
            self.do_status(None)

    def emptyline(self):
        return

    def do_help(self, args):
        print("""Commands:
    help - This help text
    profile (create|update|select) [id] - Configure profiles
    challenge (create|update|delete|select|list) - Configure challenges
    flag (create|capture|delete|list) - Configure flags in selected challenge
    twitch (init|connect|disconnect|status) - Twitch interaction
    vm (start|stop|halt|snapshot) - Configure the VM
    stream (up|down) - Start or stop the stream (Not implemented)
    status - Show information about the current state
    quit - Shut down the stream and quit the bot
        """)

    def do_profile(self, args):
        if 'create' in args:
            select = False
            channel = input("  Channel name: ")
            bot_nick = _optional_value("  Bot nick: ")
            client_id = _optional_value("  Client ID: ")
            if not self.state.twitchbot:
                select = input("  Load now? [Y/N]: ").lower() == 'y'
            profile = self.state.create_profile(channel, bot_nick, client_id, select)
            if profile:
                print(f"\nCreated profile '{profile}'")
            else:
                print("Could not create profile!")
        elif 'update' in args:
            print("\nNot implemented.... yet..")
        elif 'select' in args:
            if self.state.twitchbot:
                print("\nUnable to switch profiles after twitch has been initialized!\nPlease restart the bot")
                return
            try:
                profile = self.state.load_profile(int(args.split()[1]))
                print(f"\nSelected profile '{profile}'")
            except (TypeError, ValueError, IndexError, ProfileNotFoundError):
                print("\nPlease provide an existing profile id")
        else:
            print("""Profile commands:
    create - Create a new profile
    update - Update the selected profile
    select [id] - Select a different profile
            """)

    def do_challenge(self, args):
        if 'create' in args:
            print("  Provider: virtualbox")
            name = input("  VM name: ")
            select = input("  Select now? [Y/N]: ")
            select = select.lower() == 'y'
            challenge = self.state.create_challenge('virtualbox', name, select=select)
            if challenge:
                print(f"\nCreated challenge '{challenge}'")
            else:
                print("Could not create challenge!")
        elif 'update' in args:
            print("\nNot implemented.... yet..")
        elif 'delete' in args:
            print("\nNot implemented.... yet..")
        elif 'select' in args:
            try:
                challenge = self.state.select_challenge(int(args.split()[1]))
                if not challenge:
                    raise ChallengeNotFoundError
                print(f"\nSelected challenge '{challenge}'")
            except (TypeError, ValueError, IndexError, ProfileNotFoundError, ChallengeNotFoundError):
                print("\nPlease provide an existing challenge id")
        elif 'list' in args:
            print("\nNot implemented.... yet..")
        else:
            print("""Challenge commands:
    create - Create a new challenge
    update - Update the selected challenge
    delete [id] - Delete a challenge
    select [id] - Select a different challenge
    list - List all challenges
            """)

    def do_flag(self, args):
        if not self.state.challenge:
            print("\nChallenge not initialized!")
            args = ''
        if 'create' in args:
            flag = input("  Flag text: ")
            level = _demand_integer("  What level does the flag unlock: ")
            points = _demand_integer("  How many points does the flag reward: ")
            location = _optional_value("  Location of the flag: ")
            description = _optional_value("  Describe how to find the flag: ")
            try:
                self.state.create_flag(flag, level, points, location=location, description=description)
            except DuplicateFlagError:
                print("\nError: Flag aleady exists!")
            except NoChallengeSelectedError:
                print("\nSelect a challenge to configure flags on")
        elif 'capture' in args:
            flag = input("  flag to capture: ")
            username = input("  User to reward the flag: ")
            response = self.state.capture_flag(username.lower(), flag)
            if response and response[0] == FLAG_CAPTURED_SUCCESSFULLY:
                print(f"{username} was rewarded {response[1]} points")
            else:
                print(f"Error: Could not capture flag: {response[0]}")
        elif 'delete' in args:
            try:
                self.state.delete_flag(args[7:])
            except IndexError:
                print("Error: Please provide a flag to delete!")
            except FlagNotFoundError:
                print("Error: Flag does not exist!")
            except NoChallengeSelectedError:
                print("\nSelect a challenge to configure flags on")
        elif 'list' in args:
            try:
                print(self.state.list_flags())
            except NoChallengeSelectedError:
                print("\nSelect a challenge to configure flags on")
        else:
            print("""Flag commands:
    create - Create a new flag
    capture - Mark a flag as captured
    delete [flag] - Delete a flag
    list - List all flags
            """)

    def do_twitch(self, args):
        """
        Connect or disconnect the TwitchIO Services
        """
        if 'init' in args:
            if self.state.twitchbot:
                print("Unable to reinitialize!")
                return
            self.state.initialize_twitch()
            print(self.state.twitchbot_status())
        elif 'disconnect' in args:
            self.state.disconnect_twitch()
            print(self.state.twitchbot_status())
        elif 'connect' in args:
            self.state.connect_twitch()
            print(self.state.twitchbot_status())
        elif 'status' in args:
            print(self.state.twitchbot_status())
        else:
            print("""Twitch commands:
    init - Initialize the twitch connection
    connect - Connect the bot to IRC and PubSub websocket
    disconnect - Disconnect the bot
    status - Show the twitch bot connection status
            """)

    def do_vm(self, args):
        if not self.state.challenge or not self.state.box:
            print("\nChallenge or VM not initialized!")
            args = ''
        if 'start' in args:
            try:
                print("\nLaunching instance...")
                self.state.box.launch()
                print(f"'{self.state.box}' is now running")
            except BoxAlreadyRunningError:
                print(f"\n'{self.state.box}' is already running")
        elif 'stop' in args:
            try:
                print(f"\nSaving state and stopping '{self.state.box}'...")
                self.state.box.shut_down(True)
                print("State has been saved successfully!")
            except BoxNotRunningError:
                print(f"\n'{self.state.box}' is not running")
        elif 'halt' in args:
            try:
                print(f"\nForcefully shutting down '{self.state.box}'...")
                self.state.box.shut_down(False)
                print("Box has been shut down successfully!")
            except BoxNotRunningError:
                print(f"\n'{self.state.box}' is not running")
        elif 'snapshot' in args:
            print(f"\nTaking snapshot of '{self.state.box}'...")
            self.state.box.snapshot('Interactive mode')
            print("State has been saved successfully!")
        else:
            print("""VM commands:
    start - Start the client
    stop - Stop and save the client
    halt - Forcefully shut down the client
    snapshot - Take a snapshot of the current client state
            """)

    def do_stream(self, args):
        print("Not implemented.... yet..")

    def do_status(self, args):
        print("\n" + self.state.get_status())

    def do_quit(self, args):
        print("\nQuitting. Please wait for cleanup...")
        self.state.cleanup()
        return True

    def do_EOF(self, line):
        return self.do_quit([])
