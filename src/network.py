import subprocess
import time
import json
from plyer import notification


# Load network details from JSON file
def load_networks(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def get_available_networks():
    """Retrieve a list of available Wi-Fi networks and their details."""
    try:
        # Use netsh to list available networks with BSSID details
        result = subprocess.run(["netsh", "wlan", "show", "network", "mode=Bssid"], capture_output=True, text=True)
        networks = []
        lines = result.stdout.split('\n')
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
    except subprocess.CalledProcessError as e:
        print(f"Failed to retrieve available networks: {e}")
        return []


def create_profile_xml(ssid, password, authentication, encryption):
    """Create an XML profile for the Wi-Fi network."""
    # Adjust XML based on network authentication and encryption details
    profile_xml = f"""<?xml version="1.0"?>
<WiFiProfile>
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <authentication>{authentication}</authentication>
    <encryption>{encryption}</encryption>
    <keyMaterial>{password}</keyMaterial>
</WiFiProfile>"""
    return profile_xml


def connect_to_network(ssid, password, authentication, encryption):
    """Connect to a specified Wi-Fi network using netsh command."""
    try:
        profile_name = ssid
        profile_file = f"{profile_name}.xml"
        profile_xml = create_profile_xml(ssid, password, authentication, encryption)

        with open(profile_file, 'w') as file:
            file.write(profile_xml)

        # Add the Wi-Fi profile
        subprocess.run(["netsh", "wlan", "add", "profile", f"filename={profile_file}"], check=True)

        # Connect to the Wi-Fi network
        subprocess.run(["netsh", "wlan", "connect", "name=" + profile_name], check=True)
        print(f"Attempting to connect to {ssid}...")

        # Notify the user of the connection attempt
        notification.notify(
            title="Wi-Fi Connection Attempt",
            message=f"Attempting to connect to {ssid}...",
            timeout=10
        )

        # Clean up profile file
        subprocess.run(["del", profile_file], shell=True)

    except subprocess.CalledProcessError as e:
        print(f"Failed to connect to {ssid}: {e}")


def is_connected():
    """Check if the system is connected to the internet by pinging multiple times."""
    try:
        for _ in range(3):
            result = subprocess.run(["ping", "-n", "1", "8.8.8.8"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                return True
            time.sleep(1)  # Wait 1 second between pings
        return False
    except subprocess.CalledProcessError:
        return False


def notify_connection_status(status, ssid=None):
    """Notify the user of connection status changes."""
    if status == "connected":
        notification.notify(
            title="Wi-Fi Connected",
            message=f"Successfully connected to {ssid}!",
            timeout=10
        )
    elif status == "disconnected":
        notification.notify(
            title="Wi-Fi Disconnected",
            message="Lost internet connection.",
            timeout=10
        )


def scan():
    networks = load_networks('../networks.json')
    connected = False

    while True:
        available_networks = get_available_networks()
        if not is_connected():
            if connected:
                notify_connection_status("disconnected")
                connected = False

            print("No internet connection detected.")
            connection_successful = False

            for network in networks:
                # Find the network details from available networks
                network_details = next((n for n in available_networks if n['ssid'] == network['ssid']), None)
                if network_details:
                    print(f"Trying to connect to {network['ssid']}...")
                    connect_to_network(network['ssid'], network['password'], network_details['authentication'],
                                       network_details['encryption'])
                    time.sleep(10)  # Wait for a short period to allow the connection attempt to settle

                    if is_connected():
                        print(f"Successfully connected to {network['ssid']}!")
                        notify_connection_status("connected", ssid=network['ssid'])
                        connected = True
                        connection_successful = True
                        break

            if not connection_successful:
                print("All available networks failed. Retrying in 10 seconds.")
                time.sleep(10)  # Wait 10 seconds before retrying
        else:
            if not connected:
                notify_connection_status("connected",
                                         ssid="Current Network")  # Optionally, replace with actual network name
                connected = True
            print("Connected to the internet.")
            time.sleep(10)  # Check every 10 seconds
