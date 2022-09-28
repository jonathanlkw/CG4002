from socket import *

server_name = 'localhost'
server_port = 2022

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((server_name, server_port))

while True:
    message = input('Enter a message: ')
    client_socket.send(message.encode())

    received_msg = client_socket.recv(2048)
    print('from server: ', received_msg.decode())

    if received_msg.decode() == 'close':
        break

client_socket.close()