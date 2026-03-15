#!/bin/bash

echo "Stopping services"
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
sudo systemctl stop NetworkManager

echo "Removeing system connections AP config"
sudo rm -f /etc/NetworkManager/system-connections/*
sudo rm -f /etc/hostapd/hostapd.conf

echo "Restarting Network Manager"
sudo systemctl start NetworkManager
sleep 5

sudo nmcli device wifi hotspot ifname wlan0 ssid "Network" password "rahael5900"

echo "Checking for wlan1..."
if ip link show wlan1 &>/dev/null; then
    echo "wlan1 found, connecting to SFHSRobotics..."
    sudo ip link set wlan1 up
    sleep 2
    sudo nmcli device wifi connect "SFHSRobotics" password "MATEChamps" ifname wlan1
    echo "Enabling IP forwarding..."
    sudo sysctl -w net.ipv4.ip_forward=1
    grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf || echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
else
    echo "wlan1 not found, skipping SFHSRobotics connection."
fi

echo "Done. Hotspot Active."
nmcli connection show
ip a show wlan0
