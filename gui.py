import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


# Load network details from JSON file
def load_networks(filename):
    if not os.path.isfile(filename):
        return []
    with open(filename, 'r') as file:
        return json.load(file)


# Save network details to JSON file
def save_networks(filename, networks):
    with open(filename, 'w') as file:
        json.dump(networks, file, indent=4)


# Update the table view
def update_table():
    for row in table.get_children():
        table.delete(row)
    for network in networks:
        table.insert('', 'end', values=(network['ssid'], '•••••••••'))


# Toggle password visibility
def toggle_password():
    global password_visible
    password_visible = not password_visible
    for row in table.get_children():
        if password_visible:
            table.item(row, values=(table.item(row, 'values')[0], networks[table.index(row)]['password']))
        else:
            table.item(row, values=(table.item(row, 'values')[0], '•••••••••'))


def on_table_select(event):
    selected_item = table.selection()
    if not selected_item:
        return
    selected_row = selected_item[0]
    ssid, _ = table.item(selected_row, 'values')
    selected_network = next((net for net in networks if net['ssid'] == ssid), None)
    if selected_network:
        ssid_entry.delete(0, tk.END)
        ssid_entry.insert(0, selected_network['ssid'])
        password_entry.delete(0, tk.END)
        password_entry.insert(0, selected_network['password'])


def confirm_changes():
    ssid = ssid_entry.get()
    password = password_entry.get()
    if not ssid or not password:
        messagebox.showwarning("Input Error", "SSID and password cannot be empty.")
        return

    for network in networks:
        if network['ssid'] == ssid:
            network['password'] = password
            break
    else:
        messagebox.showwarning("Network Not Found", "SSID not found in the list.")
        return

    save_networks('networks.json', networks)
    update_table()
    messagebox.showinfo("Success", "Changes have been saved.")


def toggle_checking():
    global checking
    checking = not checking
    check_button.config(text="Turn Off" if checking else "Turn On")
    # Start or stop checking for network connections
    if checking:
        # Implement the network checking functionality here
        pass

# Initialize variables
password_visible = False
checking = False
networks = load_networks('networks.json')

# Create the main window
root = tk.Tk()
root.title("WiBye")

# Header
header_frame = tk.Frame(root)
header_frame.pack(fill=tk.X, padx=10, pady=5)
header_label = tk.Label(header_frame, text="WiBye", font=('Arial', 16, 'bold'))
header_label.pack(side=tk.LEFT)

# Toggle button
check_button = tk.Button(header_frame, text="Turn On", command=toggle_checking)
check_button.pack(side=tk.RIGHT)

# Table
table_frame = tk.Frame(root)
table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

table = ttk.Treeview(table_frame, columns=('SSID', 'Password'), show='headings')
table.heading('SSID', text='SSID')
table.heading('Password', text='Password')
table.column('Password', width=100)
table.pack(fill=tk.BOTH, expand=True)
table.bind('<<TreeviewSelect>>', on_table_select)

# Expose/Hide Password Button
expose_button = tk.Button(root, text="👁", command=toggle_password)
expose_button.pack(pady=5)

# SSID and Password Entry
entry_frame = tk.Frame(root)
entry_frame.pack(fill=tk.X, padx=10, pady=5)

tk.Label(entry_frame, text="SSID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
ssid_entry = tk.Entry(entry_frame)
ssid_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

tk.Label(entry_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
password_entry = tk.Entry(entry_frame, show='*')
password_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

# Confirm Button
confirm_button = tk.Button(root, text="Confirm Changes", command=confirm_changes)
confirm_button.pack(pady=10)


def set_gui():
    # Populate the table
    update_table()

    # Run the application
    root.mainloop()
