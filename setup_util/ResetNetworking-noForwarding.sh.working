#!/bin/bash
echo "================================================"
echo " Buoyancy Pi Network Setup"
echo "================================================"
echo ""

# -----------------------------------------------
# [1/7] Load Wi-Fi driver
# -----------------------------------------------
echo "[1/7] Loading Wi-Fi driver..."
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
# [2/7] Stop and disable conflicting services
# -----------------------------------------------
echo "[2/7] Stopping conflicting services..."
sudo systemctl stop hostapd 2>/dev/null
sudo systemctl stop dnsmasq 2>/dev/null
sudo systemctl stop NetworkManager 2>/dev/null
echo ""

# -----------------------------------------------
# [3/7] Tell NetworkManager to ignore wlan0
# -----------------------------------------------
echo "[3/7] Configuring NetworkManager to ignore wlan0..."
NM_CONF="/etc/NetworkManager/NetworkManager.conf"

# Remove any existing unmanaged-devices line to avoid duplicates
sudo sed -i '/unmanaged-devices=interface-name:wlan0/d' "$NM_CONF"

# Add keyfile section if not present
if ! grep -q "^\[keyfile\]" "$NM_CONF"; then
    echo -e "\n[keyfile]\nunmanaged-devices=interface-name:wlan0" | sudo tee -a "$NM_CONF" > /dev/null
else
    # Insert after [keyfile] line
    sudo sed -i '/^\[keyfile\]/a unmanaged-devices=interface-name:wlan0' "$NM_CONF"
fi
echo ""

# -----------------------------------------------
# [4/7] Write hostapd config
# -----------------------------------------------
echo "[4/7] Writing hostapd config..."
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

# Point hostapd to config file
sudo sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
echo ""

# -----------------------------------------------
# [5/7] Write dnsmasq config
# -----------------------------------------------
echo "[5/7] Writing dnsmasq config..."
sudo bash -c 'cat > /etc/dnsmasq.conf << EOF
interface=wlan0
dhcp-range=10.42.0.10,10.42.0.50,255.255.255.0,24h
EOF'
echo ""

# -----------------------------------------------
# [6/7] Configure static IP on wlan0
# -----------------------------------------------
echo "[6/7] Setting static IP on wlan0..."

# Make it persistent via dhcpcd
if grep -q "interface wlan0" /etc/dhcpcd.conf; then
    # Remove existing wlan0 block
    sudo sed -i '/interface wlan0/{N;N;N;d}' /etc/dhcpcd.conf
fi

sudo bash -c 'cat >> /etc/dhcpcd.conf << EOF

interface wlan0
static ip_address=10.42.0.1/24
nohook wpa_supplicant
EOF'

# Bring up wlan0 now
sudo ip addr flush dev wlan0
sudo ip addr add 10.42.0.1/24 dev wlan0
sudo ip link set wlan0 up
echo ""

# -----------------------------------------------
# [7/7] Start services and configure wlan1
# -----------------------------------------------
echo "[7/7] Starting services..."

# Start NetworkManager for wlan1
sudo systemctl start NetworkManager
sleep 3

# Clean up duplicate SFHSRobotics connections
nmcli -t -f UUID,NAME connection show | grep "SFHSRobotics" | while IFS=: read uuid name; do
    echo "Removing duplicate connection: $name ($uuid)"
    sudo nmcli connection delete "$uuid"
done

# Add SFHSRobotics on wlan1
sudo nmcli connection add \
    type wifi \
    ifname wlan1 \
    con-name "SFHSRobotics" \
    ssid "SFHSRobotics" \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "MATEChamps" \
    connection.autoconnect yes \
    connection.autoconnect-priority 5

# Unmask and enable hostapd and dnsmasq
sudo systemctl unmask hostapd
sudo systemctl enable hostapd dnsmasq
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq

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
