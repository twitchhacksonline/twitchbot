# twitchbot
Bot for Twitch Hacks Online


## Prerequisites
- Python 3.8
- Pip
- Virtualbox 6.X
- [VirtualBox 6.X Software Developer Kit](https://www.virtualbox.org/wiki/Downloads)


## Notes
Has only been developed and tested on Linux Ubuntu


# Installation on Ubuntu 18.XX or newer

First install the Downloaded VirtualBox SDK
```
cd sdk/installer
export VBOX_INSTALL_PATH='/usr/lib/virtualbox'
python vboxapisetup.py install
```

Then you can install the python project reqirements
```
pip install -r requirements.txt
```

And update the default settings `core\settings.py` to your liking


# Usage

`python twitchbot.py`

Use the `help` command in interactive mode to manage the bot
Default location for file storage of profiles and challenges are `$HOME/.config/twitchbot/`
