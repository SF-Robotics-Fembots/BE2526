#!/bin/bash

echo "================================================"
echo " Buoyancy Pi Network Setup"
echo "================================================"

echo ""
echo "[1/6] Loading Wi-Fi driver..."
sudo rmmod brcmfmac 2>/dev/null
sleep 5
sudo modprobe brcmfmac
sleep 3

# Retry up to 3 times if wlan0 doesn't appear
for i in 1 2 3; do
    if ip link show wlan0 &>/dev/null; then
        echo "wlan0 is up."
        break
    fi
    echo "wlan0 not found, retrying ($i/3)..."
    sudo rmmod brcmfmac 2>/dev/null
    sleep 5
    sudo modprobe brcmfmac
    sleep 3
done

if ! ip link show wlan0 &>/dev/null; then
    echo "ERROR: wlan0 failed to appear after 3 attempts. Check hardware."
    exit 1
fi

echo ""
echo "[2/6] Stopping services..."
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
sudo systemctl stop NetworkManager

echo ""
echo "[3/6] Disabling standalone hostapd..."
sudo systemctl disable hostapd
sudo systemctl mask hostapd

echo ""
echo "[4/6] Clearing NetworkManager connections and AP config..."
sudo rm -f /etc/NetworkManager/system-connections/*
sudo rm -f /etc/hostapd/hostapd.conf

echo ""
echo "[5/6] Restarting NetworkManager..."
sudo systemctl start NetworkManager
sleep 5

echo ""
echo "[6/6] Configuring network..."

echo "Creating hotspot on wlan0..."
sudo nmcli device wifi hotspot ifname wlan0 ssid "Network" password "rahae15900"

echo "Making hotspot permanent..."
sudo nmcli connection modify "Hotspot" connection.autoconnect yes
sudo nmcli connection modify "Hotspot" connection.autoconnect-priority 10
sudo nmcli connection modify "Hotspot" wifi.mode ap
sudo nmcli connection down "Hotspot"
sudo nmcli connection up "Hotspot"

echo "Creating SFHSRobotics connection profile for wlan1..."
sudo nmcli connection add type wifi ifname "wlan1" con-name "SFHSRobotics" ssid "SFHSRobotics" \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "MATEChamps" \
    connection.autoconnect yes \
    connection.autoconnect-priority 5

echo "Enabling IP forwarding..."
sudo sysctl -w net.ipv4.ip_forward=1
grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf || echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf

echo ""
echo "================================================"
echo " Done!"
echo "================================================"
nmcli connection show
echo ""
ip a show wlan0
ip a show wlan1 2>/dev/null
