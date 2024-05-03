import socket
import threading

# Server configuration
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5050
BUFFER_SIZE = 1024

# Maintain a list of connected clients and active sessions
clients = {}
active_sessions = {}

# Function to handle client connections
def handle_client(client_socket, client_address):
    name = client_socket.recv(BUFFER_SIZE).decode('utf-8')
    if name in active_sessions:
        client_socket.send("[ERROR] User already logged in.".encode('utf-8'))
        client_socket.close()
        return
    clients[client_socket] = name
    active_sessions[name] = client_socket
    print(f"[NEW CONNECTION] {name} connected.")
    send_user_list()

    connected = True
    while connected:
        # Receive message from client
        message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        if not message:
            break

        print(f"[MESSAGE FROM {name}] {message}")

        # Broadcast message to all clients
        broadcast_message(f"{name}: {message}")

    print(f"[DISCONNECTED] {name} disconnected.")
    del clients[client_socket]
    del active_sessions[name]
    client_socket.close()
    send_user_list()

# Function to broadcast a message to all clients
def broadcast_message(message):
    for socket in clients:
        socket.send(message.encode('utf-8'))

# Function to send the list of online users to all clients
def send_user_list():
    user_list = ','.join([name for _, name in clients.items()])
    user_list_message = f"[USERS]:{user_list}"
    for socket in clients:
        socket.send(user_list_message.encode('utf-8'))


# Main server function
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen()

    print(f"[LISTENING] Server is listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()
        print(f"[ACTIVE CONNECTIONS] {len(clients)}")

# Start the server
if __name__ == "__main__":
    start_server()