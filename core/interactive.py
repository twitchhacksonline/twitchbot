# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import cmd
import logging
from core.objects.flag import FLAG_CAPTURED_SUCCESSFULLY
from core.exceptions import ProfileNotFoundError, BoxAlreadyRunningError, BoxNotRunningError,\
    ChallengeNotFoundError, DuplicateFlagError, FlagNotFoundError, NoChallengeSelectedError,\
    ObjectiveAlreadyExists, HintNotFoundError, HintMovementError

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
    hint (create|move|delete|list) - Configure hints in selected challenge
    objective (create|override|reset|delete|list) - Configure the objective
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
                print(f"Created profile '{profile}'")
            else:
                print("Could not create profile!")
        elif 'update' in args:
            print("Not implemented.... yet..")
        elif 'select' in args:
            if self.state.twitchbot:
                print("Unable to switch profiles after twitch has been initialized!\nPlease restart the bot")
                return
            try:
                profile = self.state.load_profile(int(args.split()[1]))
                print(f"Selected profile '{profile}'")
            except (TypeError, ValueError, IndexError, ProfileNotFoundError):
                print("Please provide an existing profile id")
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
                print(f"Created challenge '{challenge}'")
            else:
                print("Could not create challenge!")
        elif 'update' in args:
            print("Not implemented.... yet..")
        elif 'delete' in args:
            print("Not implemented.... yet..")
        elif 'select' in args:
            try:
                challenge = self.state.select_challenge(int(args.split()[1]))
                if not challenge:
                    raise ChallengeNotFoundError
                print(f"Selected challenge '{challenge}'")
            except (TypeError, ValueError, IndexError, ProfileNotFoundError, ChallengeNotFoundError):
                print("Please provide an existing challenge id")
        elif 'list' in args:
            print("Not implemented.... yet..")
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
            print("Challenge not initialized!")
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
                print("Error: Flag aleady exists!")
            except NoChallengeSelectedError:
                print("Select a challenge to configure flags on")
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
                print("Select a challenge to configure flags on")
        elif 'list' in args:
            try:
                print(self.state.list_flags())
            except NoChallengeSelectedError:
                print("Select a challenge to configure flags on")
        else:
            print("""Flag commands:
    create - Create a new flag
    capture - Mark a flag as captured
    delete [flag] - Delete a flag
    list - List all flags
            """)

    def do_hint(self, args):
        if not self.state.challenge:
            print("Challenge not initialized!")
            args = ''
        if 'create' in args:
            hint = input("  Hint text: ")
            level = _demand_integer("  What level is the hint for: ")
            # cost = _demand_integer("  What is the cost of the hint: ")
            try:
                self.state.create_hint(hint, level)
            except NoChallengeSelectedError:
                print("Select a challenge to configure flags on")
        elif 'move' in args:
            print(self.state.list_hints())
            level = _demand_integer("  Level of hint to move: ")
            index = _demand_integer("  ID of hint to move: ")
            direction = None
            while direction != 'up' and direction != 'down':
                direction = input("  Direction to move hint (up|down): ")
            try:
                getattr(self.state, 'move_hint_' + direction)(level, index)
            except (NoChallengeSelectedError, HintNotFoundError, HintMovementError):
                print("Could not move hint")
        elif 'delete' in args:
            try:
                self.state.delete_hint(int(args[7:]))
            except (ValueError, IndexError):
                print("Error: Please provide a hint id to delete!")
            except HintNotFoundError:
                print("Error: Flag does not exist!")
            except NoChallengeSelectedError:
                print("Select a challenge to configure flags on")
        elif 'list' in args:
            try:
                print(self.state.list_hints())
            except NoChallengeSelectedError:
                print("Select a challenge to configure hints on")
        else:
            print("""Hint commands:
    create - Create a new hint
    move - Move a hint up/down (Hints are revealed in order top-down)
    delete [hint] - Delete a hint
    list - List all hints
            """)

    def do_objective(self, args):
        if not self.state.challenge:
            print("Challenge not initialized!")
            args = ''
        if 'create' in args:
            text = input("  Objective text: ")
            level = _demand_integer("  What level is the objective for: ")
            try:
                self.state.create_objective(text, level)
            except ObjectiveAlreadyExists:
                print(f"There is already an objective set for level {level}")
        elif 'override' in args:
            try:
                text = input("  Objective text: ")
                self.state.set_current_objective(text)
                print("Updated current objective")
            except NoChallengeSelectedError:
                print("Select a challenge to configure objectives on")
        elif 'reset' in args:
            try:
                self.state.reset_current_objective()
                print("Objective has been reset to current level")
            except NoChallengeSelectedError:
                print("Select a challenge to configure objectives on")
        elif 'delete' in args:
            try:
                level = args.split()[1]
                self.state.delete_objective(int(level))
                print(f"Deleted any objective set on level {level}")
            except (IndexError, ValueError):
                print("Error: Please provide the level to delete!")
        elif 'list' in args:
            try:
                print(self.state.list_objectives())
            except NoChallengeSelectedError:
                print("Select a challenge to configure objectives on")
        else:
            print("""Objective commands:
    create - Create a new objective
    override - Override the current objective
    reset - Reset the objective to current level
    delete [level] - Delete the objective for a level
    list - List all objectives
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
            print("Challenge or VM not initialized!")
            args = ''
        if 'start' in args:
            try:
                print("Launching instance...")
                self.state.box.launch()
                print(f"'{self.state.box}' is now running")
            except BoxAlreadyRunningError:
                print(f"'{self.state.box}' is already running")
        elif 'stop' in args:
            try:
                print(f"Saving state and stopping '{self.state.box}'...")
                self.state.box.shut_down(True)
                print("State has been saved successfully!")
            except BoxNotRunningError:
                print(f"'{self.state.box}' is not running")
        elif 'halt' in args:
            try:
                print(f"Forcefully shutting down '{self.state.box}'...")
                self.state.box.shut_down(False)
                print("Box has been shut down successfully!")
            except BoxNotRunningError:
                print(f"'{self.state.box}' is not running")
        elif 'snapshot' in args:
            print(f"Taking snapshot of '{self.state.box}'...")
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
        print("Quitting. Please wait for cleanup...")
        self.state.cleanup()
        return True

    def do_EOF(self, line):
        print("")
        return self.do_quit([])
