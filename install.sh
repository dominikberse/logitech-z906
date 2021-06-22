#!/bin/sh
set -e

CONFIG=/boot/config.txt

# install required packages
sudo apt install -y \
    git \
    python3-pip \
    pigpio \
    ir-keytable
pip3 install \
    pyserial \
    pigpio \
    evdev \
    flask \
    gunicorn \
    adafruit-circuitpython-ads1x15

# clone repository
if ! [ -d "/home/pi/logitech-z906" ]; then
  git clone https://github.com/dominikberse/logitech-z906.git /home/pi/logitech-z906
fi

# disable serial console but enable serial hardware
sudo raspi-config nonint do_serial 2
sudo raspi-config nonint do_i2c 0

# enable IR GPIO
GPIO=$(whiptail --inputbox "To which GPIO is the IR diode connected?" 20 60 "26" 3>&1 1>&2 2>&3)
if ! [ $? -eq 0 ] ; then
  return 0
fi
if ! grep -q "dtoverlay=gpio-ir" $CONFIG ; then
  sudo sed $CONFIG -i -e "\$adtoverlay=gpio-ir,gpio_pin=26"
else
  sudo sed $CONFIG -i -e "s/^.*dtoverlay=gpio-ir.*/dtoverlay=gpio-ir,gpio_pin=26/"
fi

# move bluetooth to miniuart-bt
if ! grep -q "dtoverlay=pi3-miniuart-bt" $CONFIG ; then
  sudo sed $CONFIG -i -e "\$adtoverlay=pi3-miniuart-bt"
fi

# configure logitech service
sudo tee /etc/systemd/system/logitech.service > /dev/null <<'EOF'
[Unit]
Description=media center api
After=network.target pigpiod.service

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/logitech-z906
ExecStartPre=+/usr/bin/ir-keytable -p nec
ExecStart=/home/pi/.local/bin/gunicorn --workers 1 --bind 0.0.0.0:5000 main:app

[Install]
WantedBy=multi-user.target
EOF

# append -m option to pigpiod
if ! grep -q -E "^ExecStart=.*\s+-m\b$" /lib/systemd/system/pigpiod.service ; then
  whiptail --yesno "Disable pigpiod sampling to reduce CPU usage?" 20 60
  if [ "$?" -eq 0 ] ; then
    sudo sed -i "s/^ExecStart=.*/&  -m/" /lib/systemd/system/pigpiod.service
  fi
fi

# adjust ALSA mixer
whiptail --yesno "Set USB audio as default for alsa mixer?" --defaultno 20 60
if [ "$?" -eq 0 ] ; then
  sudo sed -i "s/^defaults.ctl.card [[:digit:]]\+/defaults.ctl.card 1/" /usr/share/alsa/alsa.conf
  sudo sed -i "s/^defaults.pcm.card [[:digit:]]\+/defaults.pcm.card 1/" /usr/share/alsa/alsa.conf
fi

# enable services
sudo systemctl enable pigpiod
sudo systemctl enable logitech

# raspotify
whiptail --yesno "Install and configure raspotify?" 20 60
if [ "$?" -eq 0 ] ; then
  (curl -sL https://dtcooper.github.io/raspotify/install.sh | sh)
  DEVNAME=$(whiptail --inputbox "Enter speaker name" 20 60 "raspotify" 3>&1 1>&2 2>&3)
  if [ $? -eq 0 ] ; then
    sudo sed -i "s/^#\?DEVICE_NAME=.*$/DEVICE_NAME=\"$DEVNAME\"/" /etc/default/raspotify
  fi
fi

# reboot
whiptail --yesno "Installation complete. System needs to be rebooted.\n\nReboot now?" 20 60
if [ "$?" -eq 0 ] ; then
  sudo reboot
fi
