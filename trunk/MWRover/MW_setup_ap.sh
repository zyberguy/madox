#Define interface to configure
INTIF=wlan0

ifconfig ${INTIF} down

# Write the hostapd config file.
cat > /tmp/hostapd.conf <<EOF
interface=${INTIF}
driver=nl80211
logger_syslog=-1
logger_syslog_level=2
logger_stdout=-0
logger_stdout_level=2
dump_file=/tmp/hostapd.dump
ctrl_interface=/var/run/hostapd
ctrl_interface_group=0
ssid=MWRover
country_code=US
hw_mode=g
channel=11
beacon_int=100
#dtim_period=2
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
eapol_key_index_workaround=0
eap_server=0
own_ip_addr=127.0.0.1
EOF

hostapd /tmp/hostapd.conf -B

# Bring up the internal wifi interface.
ifconfig ${INTIF} 10.10.10.10

# Run dnsmasq, which is a combination DNS relay and DHCP server.
mkdir -p /var/lib/misc
dnsmasq -i ${INTIF} -F 10.10.10.100,10.10.10.250,15000 -K
