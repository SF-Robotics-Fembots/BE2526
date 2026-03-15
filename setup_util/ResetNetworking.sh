#!/bin/bash
echo "================================================"
echo " Buoyancy Pi Network Setup"
echo "================================================"
echo ""

# -----------------------------------------------
# [1/8] Load Wi-Fi driver
# -----------------------------------------------
echo "[1/8] Loading Wi-Fi driver..."
sudo rmmod brcmfmac 2>/dev/null
sleep 5
sudo modprobe brcmfmac
sleep 3

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

# -----------------------------------------------
# [2/8] Stop and disable conflicting services
# -----------------------------------------------
echo "[2/8] Stopping conflicting services..."
sudo systemctl stop hostapd 2>/dev/null
sudo systemctl stop dnsmasq 2>/dev/null
sudo systemctl stop NetworkManager 2>/dev/null
echo ""

# -----------------------------------------------
# [3/8] Tell NetworkManager to ignore wlan0
# -----------------------------------------------
echo "[3/8] Configuring NetworkManager to ignore wlan0..."
NM_CONF="/etc/NetworkManager/NetworkManager.conf"

sudo sed -i '/unmanaged-devices=interface-name:wlan0/d' "$NM_CONF"

if ! grep -q "^\[keyfile\]" "$NM_CONF"; then
    echo -e "\n[keyfile]\nunmanaged-devices=interface-name:wlan0" | sudo tee -a "$NM_CONF" > /dev/null
else
    sudo sed -i '/^\[keyfile\]/a unmanaged-devices=interface-name:wlan0' "$NM_CONF"
fi
echo ""

# -----------------------------------------------
# [4/8] Write hostapd config
# -----------------------------------------------
echo "[4/8] Writing hostapd config..."
sudo bash -c 'cat > /etc/hostapd/hostapd.conf << EOF
interface=wlan0
driver=nl80211
ssid=Network
hw_mode=g
channel=6
wpa=2
wpa_passphrase=rahael5900
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF'

sudo sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
echo ""

# -----------------------------------------------
# [5/8] Write dnsmasq config
# -----------------------------------------------
echo "[5/8] Writing dnsmasq config..."
sudo bash -c 'cat > /etc/dnsmasq.conf << EOF
interface=wlan0
dhcp-range=10.42.0.10,10.42.0.50,255.255.255.0,24h
EOF'
echo ""

# -----------------------------------------------
# [6/8] Configure static IP on wlan0
# -----------------------------------------------
echo "[6/8] Setting static IP on wlan0..."

if grep -q "interface wlan0" /etc/dhcpcd.conf; then
    sudo sed -i '/interface wlan0/{N;N;N;d}' /etc/dhcpcd.conf
fi

sudo bash -c 'cat >> /etc/dhcpcd.conf << EOF

interface wlan0
static ip_address=10.42.0.1/24
nohook wpa_supplicant
EOF'

sudo ip addr flush dev wlan0
sudo ip addr add 10.42.0.1/24 dev wlan0
sudo ip link set wlan0 up
echo ""

# -----------------------------------------------
# [7/8] Start services and configure wlan1
# -----------------------------------------------
echo "[7/8] Starting services..."

sudo systemctl start NetworkManager
sleep 3

nmcli -t -f UUID,NAME connection show | grep "SFHSRobotics" | while IFS=: read uuid name; do
    echo "Removing duplicate connection: $name ($uuid)"
    sudo nmcli connection delete "$uuid"
done

sudo nmcli connection add \
    type wifi \
    ifname wlan1 \
    con-name "SFHSRobotics" \
    ssid "SFHSRobotics" \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "MATEChamps" \
    connection.autoconnect yes \
    connection.autoconnect-priority 5

sudo systemctl unmask hostapd
sudo systemctl enable hostapd dnsmasq
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
echo ""

# -----------------------------------------------
# [8/8] Enable internet sharing (NAT)
# -----------------------------------------------
echo "[8/8] Enabling internet sharing..."

# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1
grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf || echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf

# Set up NAT via nftables
sudo nft flush ruleset
sudo nft add table ip nat
sudo nft add chain ip nat postrouting { type nat hook postrouting priority 100 \; }
sudo nft add rule ip nat postrouting oifname "wlan1" masquerade

# Save nftables rules so they persist across reboots
sudo nft list ruleset | sudo tee /etc/nftables.conf > /dev/null
sudo systemctl enable nftables
echo ""

echo "================================================"
echo " Done!"
echo "================================================"
echo ""
nmcli connection show
echo ""
ip a show wlan0
ip a show wlan1 2>/dev/null
echo ""
sudo systemctl status hostapd --no-pager | tail -5
