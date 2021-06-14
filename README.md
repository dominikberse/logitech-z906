# Controlling the Logitech Z906 using a Raspberry Pi

I started this project as a free-time project to integrate the Logitech Z906 sound system into my smart home, 
and to be able to stream music using Spotify Connect and other sources. In order to have full control over the
system, I desoldered the microcontroller from the control panel's circuit and solder wired the LEDs and input
buttons to a Raspberry Pi Zero W. I hooked up the required wires of the subwoofer cable and implemented a small
python service, that accepts commands from various sources (panel, IR, HTTP) and forwards them to the subwoofer.

TODO: Detailled documentation

## Overlays

Overlays need to be added in order for the serial communication to work. Add to `/boot/config.txt` under `[all]` section (at the bottom). Only applies for Raspberry Pis with wireless chip onboard (tested for Raspberry Pi Zero W).

```
dtoverlay=gpio-ir,gpio_pin=26
dtoverlay=pi3-miniuart-bt
enable_uart=1
```

## Resources

- [Logitech Z906 Protocol](https://github.com/nomis/logitech-z906/blob/main/protocol.rst) (thanks to [RomanSzabados](https://github.com/RomanSzabados))
- [IR on Raspberry Pi](https://blog.gordonturner.com/2020/05/31/raspberry-pi-ir-receiver/)
- [Logitech Z906 LIRC protocol](https://sourceforge.net/p/lirc-remotes/mailman/lirc-remotes-users/thread/55239D94.7010304%40gmail.com/#msg33739361)
- [Control panel hardware overview](https://www.reddit.com/r/hardwarehacking/comments/99eh5u/hacking_the_logitech_z906_speaker_system/)
- [Reddit post on hacking the speaker system](https://www.reddit.com/r/hardwarehacking/comments/hnpprk/hacking_the_logitech_z906_speaker_system/gfyyeng/)
