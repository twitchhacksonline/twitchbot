# twitchbot
Bot for Twitch Hacks Online


## Prerequisites
- Python 3.8
- Pip
- VirtualBox 7.x (tested on 7.2)
- [VirtualBox 7.x Software Development Kit (SDK)](https://www.virtualbox.org/wiki/Downloads)


## Notes
Has only been developed and tested on Linux Ubuntu


# Installation on Ubuntu 18.XX or newer

First install the VirtualBox SDK Python bindings
```
export VBOX_INSTALL_PATH='/usr/lib/virtualbox'
python ${VBOX_INSTALL_PATH}/sdk/installer/vboxapisetup.py install
```

Sanity check the SDK can connect to VirtualBox 7.x
```
python -c "import virtualbox; print(virtualbox.VirtualBox().version)"
```

Then you can install the python project requirements
```
pip install -r requirements.txt
```

And update the default settings `core\settings.py` to your liking


# Usage

`python twitchbot.py`

Use the `help` command in interactive mode to manage the bot
Default location for file storage of profiles and challenges are `$HOME/.config/twitchbot/`
