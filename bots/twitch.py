# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import json
import logging
import threading
from twitchio.ext import commands
from core.exceptions import NoProfileSelectedError, NoChallengeSelectedError,\
    BoxNotInitializedError, BoxNotRunningError
from core.objects.challenge import FLAG_DOES_NOT_EXIST, FLAG_ALREADY_CAPTURED, FLAG_CAPTURED_SUCCESSFULLY

logger = logging.getLogger(__name__)


class TwitchBot(commands.Bot):
    def __init__(self, state, **kwargs):
        self.state = state
        self.connection = None
        self.channel = None
        super().__init__(irc_token=kwargs['irc_token'],
                         nick=kwargs['nick'],
                         client_id=kwargs['client_id'],
                         api_token=kwargs['api_token'],
                         prefix='!',
                         initial_channels=kwargs['initial_channels'])
        logger.info("TwitchBot initialized!")
        logger.debug("Initial channels: %s", self.initial_channels)

    def __str__(self):
        return f"{self.channel} is {self.connection_status()}"

    def connection_status(self):
        return "connected" if self.connection else "not connected"

    def connect(self):
        if self.loop.is_running():
            logger.error("Twitch services are already connected")
            return
        logger.info("Connecting to Twitch services...")
        self.connection = threading.Thread(target=self.run, args=())
        self.connection.start()

    def disconnect(self):
        if not self.loop or not self.loop.is_running():
            logger.error("Twitch services are not connected")
            return
        logger.info("Disconnecting from Twitch services...")
        self.loop.stop()
        while self.loop.is_running():
            pass
        self.connection = None

    # region websocket
    async def event_ready(self):
        subscriptions = self.state.get_subscriptions()
        self.listener = await self.pubsub_subscribe(self.http.token, *subscriptions)
        self.channel = self.get_channel(self.initial_channels[0])
        await self.channel.send('Bot initialized! Type !help to learn how to interact with me')

    async def _parse_response(self, data):
        subscriptions = self.state.get_subscriptions()
        if data.get('error'):
            logger.error("Failed to subscribe to %s", subscriptions)
        elif not data.get('nonce'):
            await self.channel.send('You are sending messages too fast, please slow down!')
        else:
            logger.info("Subscribed to %s", subscriptions)

    async def _parse_channel_points(self, data):
        message = json.loads(data.get('data').get('message'))
        if message.get('type') == 'reward-redeemed':
            redemption = message.get('data').get('redemption')
            logger.debug("User redeemed points %s", redemption)
            user = redemption.get('user').get('display_name')
            reward = redemption.get('reward').get('title')
            cost = redemption.get('reward').get('cost')
            logger.info(f'{user} redeemed {reward}')
            # TODO: Handle rewards in self.state.redeemed_channel_points()
            if 'hotseat' in reward:
                if self.state.get_hotseat():
                    await self.channel.send("Sorry! Hotseat is not available at the moment..")
                else:
                    self.state.set_hotseat(user, cost)
                    await self.channel.send(
                        f"{user} is now in the hotseat, and has exclusive control for the next 5 minutes"
                    )
            elif reward == 'Hints':
                await self.channel.send(self.state.reveal_hint())

    async def _parse_bits(self, data):
        message = json.loads(data.get('data').get('message'))
        username = message.get('data').get('user_name')
        amount = message.get('data').get('bits_used')
        logger.info(f'{username} cheered {amount}')

    async def _parse_subscribe(self, data):
        message = json.loads(data.get('data').get('message'))
        username = message.get('display_name')
        amount = message.get('cumulative_months')
        gift = message.get('is_gift')
        logger.info(f'{username} has subscribed for {amount} months')
        if not gift:
            if amount == 1:
                await self.channel.send(f'{username} is a new subscriber. Thank you!')
            else:
                await self.channel.send(f'{username} has been subscribed for a total of {amount} months. Thank you!')

    async def _parse_follow(self, data):
        pass

    async def _parse_mod_action(self, data):
        message = json.loads(data.get('data').get('message'))
        action = message.get('data').get('moderation_action')
        username = message.get('data').get('created_by')
        args = message.get('data').get('args')
        logger.info(f'{username} moderated {action}: {args}')

    async def _parse_whisper(self, data):
        try:
            message = json.loads(data.get('data').get('message'))
            message_data = json.loads(message.get('data'))
            body = message_data.get('body')
            login = message_data.get('tags').get('login')
            logger.debug("Whisper message: %s", message_data)
            if login != self.nick:
                logger.info(f"Received whisper: {body} from {login}")
                result = self.state.capture_flag(login, body)
                # Whispers are kinda broken
                # They require the user to close and reopen the whisper box to see the response
                # Not sure why that happens
                if result == FLAG_DOES_NOT_EXIST:
                    await self._ws.send_privmsg(self.channel.name, f".w {login} Flag not recognized")
                elif result == FLAG_CAPTURED_SUCCESSFULLY:
                    await self._ws.send_privmsg(self.channel.name, f".w {login} Flag has been captured!")
                elif result == FLAG_ALREADY_CAPTURED:
                    await self._ws.send_privmsg(self.channel.name, f".w {login} Flag was already captured")
        except AttributeError:
            logger.warning("Could not decode whisper")

    async def event_raw_pubsub(self, data):
        if data.get('type') == 'RESPONSE':
            await self._parse_response(data)
        elif data.get('type') == 'PONG':
            pass
        elif data.get('type') == 'MESSAGE':
            try:
                topic = data.get('data').get('topic')
                if topic.startswith('channel-points-channel-v1'):
                    await self._parse_channel_points(data)
                elif topic.startswith('channel-bits-events-v2'):
                    await self._parse_bits(data)
                elif topic.startswith('channel-subscribe-events-v1'):
                    await self._parse_subscribe(data)
                elif topic.startswith('chat_moderator_actions'):
                    await self._parse_mod_action(data)
                elif topic.startswith('whispers'):
                    await self._parse_whisper(data)
            except (ValueError, KeyError):
                logger.exception("Unable to parse pubsub message")
        else:
            logger.warning("Unrecognized PubSub message: %s", data)

    async def event_message(self, message):
        logger.debug("Received message: %s", message.content)
        await self.handle_commands(message)
    # endregion websocket

    async def event_command_error(self, ctx, error):
        # Ignore if an erroneous command is sent to the bot
        return

    # region general commands
    @commands.command(name='help')
    async def show_help(self, ctx, *args):
        # TODO: Set help text in state, save in profile
        help_text = """
            Info and rules are listed in the panels below the stream |
            '!type your text' to type text |
            '!execute your command' to execute commands (enter at end of line) |
            '!press keys' to send special key commands |
            '!release' to release stuck modifier keys
            """
        if ctx.author.is_mod:
            if 'mod' in args:
                help_text = """
                '!hotseat [username]' |
                '!allow username(s)' |
                '!deny username(s)' |
                '!remove username(s)' |
                '!stop [halt] [restore]' stop, forcefully halt or restore the VM |
                '!snap' snapshot the current VM state |
                '!delay [ms] [seconds]' override keypress delay
                """
            else:
                help_text += " | '!help mod' for moderator commands"
        await ctx.send(help_text)

    @commands.command(name='objective', aliases=['obj', 'what'])
    async def show_objective(self, ctx):
        objective = "There is no objective set at the moment"
        try:
            objective = self.state.get_current_objective()
        except NoChallengeSelectedError:
            pass
        objective_text = objective + """ |
            Be respectful of others |
            No destructive behaviour |
            All rules can be found in the panels below the stream
            """
        await ctx.send(objective_text)

    @commands.command(name='source', aliases=['github', 'gh'])
    async def show_source(self, ctx):
        source_text = "The source for this bot is here: https://github.com/twitchhacksonline/twitchbot"
        await ctx.send(source_text)

    @commands.command(name='discord')
    async def discord_link(self, ctx):
        try:
            link = self.state.profile.discord
            if link:
                await ctx.send(f"Discord server for these challenges: {self.state.profile.discord}")
        except AttributeError:
            pass
    # endregion general commands

    # region challenge interaction
    async def can_interact(self, ctx):
        interact = self.state.allow_interaction(ctx.author)
        if not interact[0] and interact[1]:
            await ctx.send(interact[1])
        return interact[0]

    @commands.command(name='type', aliases=['t'])
    async def type_input(self, ctx, *args):
        if not args:
            return
        try:
            if await self.can_interact(ctx):
                # TODO: self.state.new_interaction()
                prefix = ctx.message.content.split(' ')[0]
                command = ctx.message.content[len(prefix)+1:]
                self.state.type_text(command)
                await ctx.send(f"Typed: '{command}'"[:500])
        except (ValueError, IndexError, AttributeError) as e:
            logger.exception(e)
        except (NoChallengeSelectedError, BoxNotInitializedError):
            await ctx.send("There is no challenge running at the moment, please stand by..")
        except BoxNotRunningError:
            await ctx.send("Instance is not running, attempting to restart it...")
            self.state.start_challenge()

    @commands.command(name='execute', aliases=['e'])
    async def execute_line(self, ctx, *args):
        try:
            if await self.can_interact(ctx):
                # TODO: self.state.new_interaction()
                if args:
                    prefix = ctx.message.content.split(' ')[0]
                    command = ctx.message.content[len(prefix)+1:]
                    self.state.type_text(command)
                    self.state.send_keys(['enter'])
                    await ctx.send(f"Executed: '{command}'"[:500])
                else:
                    command = self.state.send_keys(['enter'])
                    if command:
                        keys_sent = ' '.join(command)
                        await ctx.send(f"Pressed: '{keys_sent}'")
        except (ValueError, IndexError, AttributeError) as e:
            logger.exception(e)
        except (NoChallengeSelectedError, BoxNotInitializedError):
            await ctx.send("There is no challenge running at the moment, please stand by..")
        except BoxNotRunningError:
            await ctx.send("Instance is not running, attempting to restart it...")
            self.state.start_challenge()

    @commands.command(name='press', aliases=['p'])
    async def press_keys(self, ctx, *args):
        try:
            if await self.can_interact(ctx):
                if len(args) == 0:
                    await ctx.send(f"Special keys: {self.state.get_special_keys()}")
                else:
                    # TODO: self.state.new_interaction()
                    command = self.state.send_keys(args)
                    if command:
                        keys_sent = ' '.join(command)
                        await ctx.send(f"Pressed: '{keys_sent}'")
                    else:
                        await ctx.send(f"Special keys: {self.state.get_special_keys()}")
        except (ValueError, IndexError, AttributeError) as e:
            logger.exception(e)
        except (NoChallengeSelectedError, BoxNotInitializedError):
            await ctx.send("There is no challenge running at the moment, please stand by..")
        except BoxNotRunningError:
            await ctx.send("Instance is not running, attempting to restart it...")
            self.state.start_challenge()

    @commands.command(name='release')
    async def release_keys(self, ctx, *args):
        try:
            if await self.can_interact(ctx):
                self.state.release_keys()
                await ctx.send('Released all modifier keys')
        except (NoChallengeSelectedError, BoxNotInitializedError, BoxNotRunningError):
            await ctx.send("There is no challenge running at the moment, please stand by..")
    # endregion challenge interaction

    # region user handling
    @commands.command(name='hotseat', aliases=['hs'])
    async def hotseat_user(self, ctx, *args):
        if ctx.author.is_mod:
            if len(args) > 0:
                try:
                    seconds = int(args[1])
                except (IndexError, ValueError):
                    seconds = None
                self.state.set_hotseat(args[0], seconds=seconds)
            else:
                self.state.set_hotseat(None)
        username = self.state.get_hotseat()
        if username:
            await ctx.send(f"{username} is in the hotseat, and is the only one that can interact with the machine")
        else:
            await ctx.send("Hotseat is empty, anyone with the permission can interact")

    @commands.command(name='allow')
    async def allow_users(self, ctx, *args):
        if not ctx.author.is_mod:
            return
        try:
            self.state.allow_users(args)
        except NoProfileSelectedError:
            await ctx.send("Could not add users to list")

    @commands.command(name='deny')
    async def deny_users(self, ctx, *args):
        if not ctx.author.is_mod:
            return
        try:
            self.state.deny_users(args)
        except NoProfileSelectedError:
            await ctx.send("Could not add users to list")

    @commands.command(name='remove')
    async def remove_user(self, ctx, *args):
        if not ctx.author.is_mod:
            return
        try:
            self.state.reset_users(args)
        except NoProfileSelectedError:
            await ctx.send("Could not reset users")
    # endregion user handling

    # region box control
    @commands.command(name='stop')
    async def shut_down(self, ctx, *args):
        if not ctx.author.is_mod:
            return
        if args:
            if args[0] == 'restore':
                try:
                    self.state.stop_challenge()
                except BoxNotRunningError:
                    pass
                try:
                    self.state.start_challenge(restore=True)
                    await ctx.send("Most recent snapshot has been restored")
                except (NoChallengeSelectedError, BoxNotInitializedError):
                    await ctx.send("Could not restore snapshot")
            if args[0] == 'halt':
                try:
                    self.state.stop_challenge(save=False)
                    await ctx.send("System is now in 'powered off' state")
                except (NoChallengeSelectedError, BoxNotInitializedError, BoxNotInitializedError):
                    await ctx.send("System is not running")
        else:
            try:
                self.state.stop_challenge(save=True)
                await ctx.send("System is now in 'saved' state")
            except (NoChallengeSelectedError, BoxNotInitializedError, BoxNotInitializedError):
                await ctx.send("System is not running")

    @commands.command(name='snap')
    async def snapshot(self, ctx, *args):
        if not ctx.author.is_mod:
            return
        try:
            self.state.snapshot_challenge(ctx.author.name)
            await ctx.send("Snapshot created!")
        except (NoChallengeSelectedError, BoxNotInitializedError):
            await ctx.send("No system to take snapshot of")

    @commands.command(name='delay')
    async def press_delay(self, ctx, *args):
        if not ctx.author.is_mod:
            return
        try:
            if not args:
                delay = self.state.get_press_delay()
                response = f"Press delay is {delay}ms"
            else:
                delay = int(args[0])
                response = f"Press delay is now {delay}ms"
                expiry = None
                if len(args) > 1:
                    expiry = int(args[1])
                    response += f" for the next {expiry} seconds"
                self.state.set_press_delay(delay, expiration=expiry)
            await ctx.send(response)
        except (NoChallengeSelectedError, BoxNotInitializedError):
            await ctx.send("There is no challenge running at the moment, please stand by..")
        except ValueError:
            await ctx.send("Please provide integer values for delay and expiry")
    # endregion box control
