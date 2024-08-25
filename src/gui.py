import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from network import scan, stop_scan
from threading import Thread

from src.entries import set_entry

NETWORKS_FILE = '../networks.json'
ICONS = {
    'hide': '../assets/hide_icon.png',
    'show': '../assets/show_icon.png',
    'current_on': '../assets/current_on.png',
    'current_off': '../assets/current_off.png',
    'edit': '../assets/check.png',
    'add': '../assets/add.png',
    'remove': '../assets/remove.png'
}


# Load network details from JSON file
def load_networks(filename):
    if not os.path.isfile(filename):
        set_entry('networks', [])
        return []
    with open(filename, 'r') as file:
        value = json.load(file)
        set_entry('networks', value)
        return value


# Save network details to JSON file
def save_networks(filename, networks):
    with open(filename, 'w') as file:
        json.dump(networks, file, indent=4)
        set_entry('networks', networks)


# Update the table view
def update_table():
    for row in table.get_children():
        table.delete(row)
    for network in networks:
        table.insert('', 'end', values=(network['ssid'], '*' * len(network['password'])))


def on_enter(event):
    """Change the border color when the mouse enters the button."""
    event.widget.config(background='lightGray', highlightcolor='blue', relief="sunken")


def on_leave(event):
    """Revert the border color when the mouse leaves the button."""
    event.widget.config(background='SystemButtonFace', highlightcolor='lightGray', relief="groove", borderwidth=0)


def apply_hover_effects(root):
    """Apply hover effects to all buttons in the root window."""
    for widget in root.winfo_children():
        if isinstance(widget, tk.Button):
            widget.config(buttonStyle)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        # If buttons are inside frames or other containers, you need to recursively apply hover effects
        elif isinstance(widget, tk.Frame) or isinstance(widget, tk.Toplevel):
            apply_hover_effects(widget)


# Toggle password visibility
def toggle_password():
    global password_visible
    password_visible = not password_visible
    for row in table.get_children():
        if password_visible:
            expose_button.config(image=hide_icon)
            password_entry.config(show='*')
        else:
            expose_button.config(image=show_icon)
            password_entry.config(show='')


def on_table_select(event):
    global last_selected_item
    selected_item = table.selection()

    if len(selected_item) == 0:
        confirm_button.pack_forget()
        add_button.pack(pady=10)
        remove_button.pack_forget()
    else:
        confirm_button.pack(pady=10, side=tk.LEFT, padx=10)
        remove_button.pack(padx=10, side=tk.LEFT)
        add_button.pack_forget()

    if last_selected_item == selected_item:
        table.selection_remove(list(last_selected_item))
        last_selected_item = None
        ssid_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
    else:
        last_selected_item = selected_item
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

    save_networks(NETWORKS_FILE, networks)
    update_table()
    messagebox.showinfo("Success", "Changes have been saved.")


def remove_entry():
    selected_item = table.selection()
    if selected_item:
        # Ask for confirmation before removing the entry
        response = messagebox.askyesno("Confirm Removal", "Are you sure you want to remove the selected entry?")
        if response:
            item = None
            selected_row = selected_item[0]
            ssid, _ = table.item(selected_row, 'values')
            for network in networks:
                if network.get("ssid") == ssid:
                    item = network
            if item:
                networks.remove(item)
    save_networks(NETWORKS_FILE, networks)
    update_table()
    messagebox.showinfo("Success", "Changes have been saved.")


def add_entry():
    ssid = ssid_entry.get()
    password = password_entry.get()
    if not ssid or not password:
        messagebox.showwarning("Input Error", "SSID and password cannot be empty.")
        return

    # Avoids duplications
    for network in networks:
        if network['ssid'] == ssid:
            messagebox.showwarning("Network Already Exists", "SSID already exists in the list.")
            return

    networks.append({"ssid": ssid, "password": password})
    save_networks(NETWORKS_FILE, networks)
    update_table()
    messagebox.showinfo("Success", "Changes have been saved.")


def toggle_checking():
    global checking
    global scan_thread

    checking = not checking
    if checking:
        check_button.config(image=current_on)
        scanning_label.config(text="Scanning")
        start_scanning(scan_thread)
    else:
        scanning_label.config(text="Not scanning")
        check_button.config(image=current_off)
        stop_scan()
        scan_thread = Thread(target=scan, daemon=True)


def start_scanning(thread: Thread):
    """Start scanning for networks periodically."""
    thread.start()


def on_closing():
    stop_scan()
    root.destroy()


# Initialize variables
password_visible = False
checking = False
networks = load_networks(NETWORKS_FILE)
scan_thread: Thread = Thread(target=scan, daemon=True)

# Create the main window
root = tk.Tk()
root.geometry("350x420")
root.resizable(False, False)
root.title("WiBye")
root.iconbitmap("../assets/app_icon.ico")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Create style Object
buttonStyle = {"relief": "groove", "borderwidth": 0,
               "highlightthickness": 0}

hide_icon = tk.PhotoImage(file=ICONS['hide'])
show_icon = tk.PhotoImage(file=ICONS['show'])
current_on = tk.PhotoImage(file=ICONS['current_on'])
current_off = tk.PhotoImage(file=ICONS['current_off'])
edit = tk.PhotoImage(file=ICONS['edit'])
add = tk.PhotoImage(file=ICONS['add'])
remove = tk.PhotoImage(file=ICONS['remove'])

# Header
header_frame = tk.Frame(root)
header_frame.pack(fill=tk.X, padx=10, pady=5)
header_label = tk.Label(header_frame, text="WiBye", font=('Arial', 16, 'bold'))
header_label.pack(side=tk.LEFT)

# Toggle button
check_button = tk.Button(header_frame, image=current_off, command=toggle_checking)
check_button.pack(side=tk.RIGHT)

scanning_label = tk.Label(header_frame, text="Not scanning", padx=10,
                          font=('Arial', 9, 'normal'))
scanning_label.pack(side=tk.RIGHT)

# Table
table_frame = tk.Frame(root)
table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
last_selected_item = None

table = ttk.Treeview(table_frame, columns=('SSID', 'Password'), show='headings')
table.heading('SSID', text='SSID')
table.heading('Password', text='Password')
table.column('Password', width=100)
table.pack(fill=tk.BOTH, expand=True)
table.bind('<<TreeviewSelect>>', on_table_select)

# SSID and Password Entry
entry_frame = tk.Frame(root)
entry_frame.pack(fill=tk.X, padx=10, pady=5)

tk.Label(entry_frame, text="SSID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
ssid_entry = tk.Entry(entry_frame, width=35)
ssid_entry.grid(row=0, column=1, pady=5, padx=5)

tk.Label(entry_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
password_entry = tk.Entry(entry_frame, show='*', width=35)
password_entry.grid(row=1, column=1, pady=5, padx=5)

# Expose/Hide Password Button
expose_button = tk.Button(entry_frame, image=show_icon, command=toggle_password)
expose_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.EW)

hstack = tk.Frame(root, height=24)
hstack.pack(expand=True)

# Confirm Button
confirm_button = tk.Button(hstack, image=edit,
                           command=confirm_changes)

# Remove Button
remove_button = tk.Button(hstack, image=remove, command=remove_entry)

# Add Button
add_button = tk.Button(hstack, image=add, command=add_entry)
add_button.pack(pady=10)

apply_hover_effects(root)


def gui():
    # Populate the table
    update_table()
    # Run the application
    root.mainloop()
    scan_thread.join()


__all__ = [gui, networks]
