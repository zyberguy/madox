#!/bin/sh

#MWRover - Mecanum Wheel Rover Base
#http://www.madox.net/

#Stop Chumby Control Panel
/usr/chumby/scripts/stop_control_panel
#Kill all the useless Chumby/internet related processes
killall chumbradiod cpid ntpd crond chumbhowld chumbalarmd
#Self-promotion line
/usr/bin/imgtool --mode=draw madox.png
