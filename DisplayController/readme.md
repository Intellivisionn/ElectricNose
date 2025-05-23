sudo python3 adafruit-pitft.py --display=28r --rotation=270 --install-type=console

check devices:
ls -l /dev/fb*
ls -l /dev/dri/*
dmesg | grep -i 'drm\|vc4'

dont forget to:
sudo chmod 666 /dev/dri/card2
sudo chmod 666 /dev/dri/renderD128