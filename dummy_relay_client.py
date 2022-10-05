from socket import *

server_name = 'localhost'
server_port = 2021

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((server_name, server_port))

def send_plaintext(remote_socket, msg):
    success = True
    plaintext = msg

    # ice_print_debug(f"Sending message to client: {plaintext} (Unencrypted)")
    # send len followed by '_' followed by cypher
    m = str(len(plaintext))+'_'
    try:
        remote_socket.sendall(m.encode("utf-8"))
        remote_socket.sendall(plaintext.encode("utf-8"))
    except OSError:
        print("Connection terminated")
        success = False
    return success

while True:
    try:
        #To be replaced with actual packets
        move_data = input('Enter a move: ')
        #client_socket.send(move_data.encode('utf-8'))
        send_plaintext(client_socket, move_data)
    except ConnectionError:
        print('Connection lost')
        client_socket.close()
        break

