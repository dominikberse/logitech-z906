# Logitech Z906 Controller
Project to replace the Logitech Z906 controller with a Raspberry Pi Zero W.

## Overlays

Overlays need to be added in order for the serial communication to work. Add to `/boot/config.txt` under `[all]` section (at the bottom).

```
dtoverlay=gpio-ir,gpio_pin=26
dtoverlay=pi3-miniuart-bt
enable_uart=1
```
