import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

# Server configuration
SERVER_HOST = '172.31.19.30'  # Replace 'server_ip_address' with the actual IP address of the server
SERVER_PORT = 5050
BUFFER_SIZE = 1024

class ChatClient:
    def __init__(self, root):
        self.name = ""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.private_chat_windows = {}
        self.logged_in_users = []  # List to store logged-in usernames
        self.root = root
        self.setup_login_gui()

    def setup_login_gui(self):
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("Login")
        self.login_window.geometry("300x150")
        self.login_window.configure(bg='#e6e6e6')

        self.name_label = tk.Label(self.login_window, text="Enter your name:", bg='#e6e6e6', fg='#333333')
        self.name_label.pack()

        self.name_entry = tk.Entry(self.login_window, bg='#ffffff', fg='#333333', insertbackground='#333333')
        self.name_entry.pack()

        self.password_label = tk.Label(self.login_window, text="Enter your password:", bg='#e6e6e6', fg='#333333')
        self.password_label.pack()

        self.password_entry = tk.Entry(self.login_window, show="*", bg='#ffffff', fg='#333333', insertbackground='#333333')
        self.password_entry.pack()

        self.login_button = tk.Button(self.login_window, text="Login", command=self.login, bg='#ffffff', fg='#000000')
        self.login_button.pack()

    def login(self):
        self.name = self.name_entry.get()
        if self.name:
            if self.name in self.logged_in_users:
                messagebox.showerror("Error", "User with the same name is already logged in. Please choose a different name.")
            else:
                password = self.password_entry.get()
                if password == self.name + '1234':
                    self.logged_in_users.append(self.name)
                    self.login_window.destroy()
                    self.setup_chat_gui()
                    self.connect_to_server()
                else:
                    messagebox.showerror("Error", "Invalid password.")
        else:
            messagebox.showerror("Error", "Please enter your name.")

    def setup_chat_gui(self):
        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title("Chat Client")
        self.chat_window.geometry("800x400")
        self.chat_window.configure(bg='#e6e6e6')

        self.chat_history = scrolledtext.ScrolledText(self.chat_window, width=60, height=20, state='disabled',
                                                       bg='#ffffff', fg='#333333', insertbackground='#333333')
        self.chat_history.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.message_frame = tk.Frame(self.chat_window, bg='#e6e6e6')
        self.message_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.message_entry = tk.Entry(self.message_frame, width=50, bg='#ffffff', fg='#333333', insertbackground='#333333')
        self.message_entry.pack(side=tk.LEFT, padx=5)

        self.send_button = tk.Button(self.message_frame, text="Send", command=self.send_message, bg='#ffffff', fg='#000000')
        self.send_button.pack(side=tk.RIGHT, padx=5)

        self.user_frame = tk.Frame(self.chat_window, bg='#e6e6e6')
        self.user_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="ns")

        self.user_list_label = tk.Label(self.user_frame, text="Users Online:", bg='#e6e6e6', fg='#333333')
        self.user_list_label.pack()

        self.user_list = tk.Listbox(self.user_frame, width=20, height=20, bg='#ffffff', fg='#333333', selectbackground='#007acc', selectforeground='#ffffff')
        self.user_list.pack(fill=tk.BOTH, expand=True)
        self.user_list.bind("<Double-Button-1>", self.start_private_chat)

    def connect_to_server(self):
        try:
            self.client.connect((SERVER_HOST, SERVER_PORT))
            self.client.send(self.name.encode('utf-8'))
            self.connected = True
            threading.Thread(target=self.receive_messages).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to server: {str(e)}")
            self.root.destroy()

    def receive_messages(self):
        while self.connected:
            try:
                message = self.client.recv(BUFFER_SIZE).decode('utf-8')
                if not message:
                    break
                if message.startswith("[USERS]"):
                    users = message.split(":")[1].split(",")
                    self.update_user_list(users)
                elif message.startswith("[PRIVATE MESSAGE]"):
                    self.handle_private_message(message)
                else:
                    self.display_message(message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def send_message(self):
        message = self.message_entry.get()
        if message:
            try:
                self.client.send(message.encode('utf-8'))
                self.message_entry.delete(0, 'end')
            except Exception as e:
                print(f"Error sending message: {e}")
                messagebox.showerror("Error", "Failed to send message. Connection lost.")
                self.connected = False
                self.root.destroy()

    def display_message(self, message):
        self.chat_history.configure(state='normal')
        self.chat_history.insert(tk.END, message + '\n')
        self.chat_history.configure(state='disabled')

    def update_user_list(self, users):
        self.user_list.delete(0, tk.END)
        for user in users:
            self.user_list.insert(tk.END, user)

    def start_private_chat(self, event):
        selection = self.user_list.curselection()
        if selection:
            user = self.user_list.get(selection)
            if user != self.name:
                if user not in self.private_chat_windows:
                    self.create_private_chat_window(user)

    def handle_private_message(self, message):
        sender, content = message.split(":", 1)
        sender = sender.split("[PRIVATE MESSAGE] ")[1].strip()
        content = content.strip()
        if sender != self.name:
            if sender not in self.private_chat_windows:
                self.create_private_chat_window(sender)
            _, chat_history = self.private_chat_windows[sender]
            chat_history.configure(state='normal')
            chat_history.insert(tk.END, f"{sender}: {content}\n")
            chat_history.configure(state='disabled')

    def create_private_chat_window(self, user):
        private_chat_window = tk.Toplevel(self.root)
        private_chat_window.title(f"Private Chat with {user}")
        private_chat_window.geometry("400x300")
        private_chat_window.configure(bg='#e6e6e6')

        chat_history = scrolledtext.ScrolledText(private_chat_window, width=50, height=15, state='disabled',
                                                  bg='#ffffff', fg='#333333', insertbackground='#333333')
        chat_history.pack(padx=5, pady=5)

        message_frame = tk.Frame(private_chat_window, bg='#e6e6e6')
        message_frame.pack(padx=5, pady=5)

        message_entry = tk.Entry(message_frame, width=40, bg='#ffffff', fg='#333333', insertbackground='#333333')
        message_entry.pack(side=tk.LEFT, padx=5)

        send_button = tk.Button(message_frame, text="Send", command=lambda: self.send_private_message(user, message_entry),
                                bg='#ffffff', fg='#000000')
        send_button.pack(side=tk.RIGHT, padx=5)

        message_entry.bind("<Return>", lambda event: self.send_private_message(user, message_entry))

        self.private_chat_windows[user] = (private_chat_window, chat_history)

    def send_private_message(self, recipient, message_entry):
        message = message_entry.get()
        if message:
            try:
                self.client.send(f"[PRIVATE MESSAGE] {recipient}: {message}".encode('utf-8'))
                _, chat_history = self.private_chat_windows[recipient]
                chat_history.configure(state='normal')
                chat_history.insert(tk.END, f"{self.name}: {message}\n")
                chat_history.configure(state='disabled')
                message_entry.delete(0, 'end')
            except Exception as e:
                print(f"Error sending private message: {e}")
                messagebox.showerror("Error", "Failed to send message. Connection lost.")
                self.connected = False
                self.root.destroy()

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    chat_client = ChatClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()