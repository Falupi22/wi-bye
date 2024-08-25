import subprocess
import time
import json
import os
import socket
from plyer import notification

from src.entries import get_entry

SCAN_INTERVAL = 10
CONNECTION_INTERVAL = 5

scanning = False


def add_quotes(string, quote_type='"'):
    """
    Encloses the given string in quotes.

    Parameters:
    string (str): The string to be enclosed in quotes.
    quote_type (str): The type of quote to use, either single (') or double ("). Defaults to double quotes.

    Returns:
    str: The string enclosed in the specified quotes.
    """
    return f"{quote_type}{string}{quote_type}"


# Load network details from JSON file
def load_networks(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def get_available_networks():
    """Retrieve a list of available Wi-Fi networks and their details."""
    try:
        # Use netsh to list available networks with BSSID details
        result = os.popen("netsh wlan show network mode=Bssid").read()
        networks = []
        lines = result.split('\n')
        current_network = {}
        for line in lines:
            if "SSID" in line and not "BSSID" in line:
                if current_network:
                    networks.append(current_network)
                current_network = {"ssid": line.split(":")[1].strip()}
            elif "Authentication" in line:
                current_network["authentication"] = line.split(":")[1].strip()
            elif "Encryption" in line:
                current_network["encryption"] = line.split(":")[1].strip()
        if current_network:
            networks.append(current_network)
        return networks
    except Exception as e:
        print(f"Failed to retrieve available networks: {e}")
        return []


def create_profile_xml(ssid, password, authentication, encryption):
    """Create an XML profile for the Wi-Fi network."""
    # Adjust XML based on network authentication and encryption details
    profile_xml = """<?xml version=\"1.0\"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>""" + ssid + """</name>
    <SSIDConfig>
        <SSID>
            <name>""" + ssid + """</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>""" + password + """</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>"""
    return profile_xml


def connect_to_network(ssid, password, authentication, encryption):
    """Connect to a specified Wi-Fi network using netsh command."""
    try:
        profile_name = ssid
        profile_file = f"{profile_name}.xml"
        profile_xml = create_profile_xml(ssid, password, authentication, encryption)

        relative_path = "..\\" + profile_file
        with open(relative_path, 'w') as file:
            file.write("..\\" + profile_xml)

        os.system("netsh wlan add profile filename=" + add_quotes(relative_path))

        os.system("netsh wlan connect name=" + add_quotes(ssid) +
                  " ssid=" + add_quotes(ssid))

        os.system("del " + add_quotes(relative_path))

    except Exception as e:
        print(f"Failed to connect to {ssid}: {e}")


def is_connected(attempts=3, timeout=3):
    """Check if the system is connected to the internet by pinging multiple times."""
    for attempt in range(attempts):
        try:
            # Try to connect to the host
            socket.setdefaulttimeout(timeout)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("8.8.8.8", 53))
            return True
        except socket.error as ex:
            print(f"Attempt {attempt + 1} failed: {ex}")
            # Wait before retrying
            time.sleep(1)
    return False


def notify_connection_status(status, ssid=None):
    """Notify the user of connection status changes."""
    if status == "connected":
        notification.notify(
            title="Wi-Fi Connected",
            message=f"Successfully connected to {ssid}!",
            timeout=3
        )
    elif status == "disconnected":
        notification.notify(
            title="Wi-Fi Disconnected",
            message="Lost internet connection.",
            timeout=3
        )


def scan():
    global scanning
    networks = get_entry("networks")
    connected = False

    scanning = True
    while scanning:
        available_networks = get_available_networks()
        if not is_connected():
            if connected:
                notify_connection_status("disconnected")
                connected = False

            connection_successful = False

            for network in networks:
                # Find the network details from available networks
                network_details = next((n for n in available_networks if n['ssid'] == network['ssid']), None)
                if network_details:
                    connect_to_network(network['ssid'], network['password'], network_details['authentication'],
                                       network_details['encryption'])
                    time.sleep(CONNECTION_INTERVAL)  # Wait for a short period to allow the connection attempt to settle

                    if is_connected():
                        notify_connection_status("connected", ssid=network['ssid'])
                        connected = True
                        connection_successful = True
                        break

            if not connection_successful:
                time.sleep(SCAN_INTERVAL)  # Wait 10 seconds before retrying
        else:
            if not connected:
                notify_connection_status("connected",
                                         ssid="Current Network")  # Optionally, replace with actual network name
                connected = True
            time.sleep(SCAN_INTERVAL)  # Check every 10 seconds


def stop_scan():
    global scanning
    scanning = False
