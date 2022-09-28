from socket import *

server_name = 'localhost'
server_port = 2021

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((server_name, server_port))

while True:
    try:
        move_data = input('Enter a move: ')
        client_socket.send(move_data.encode('utf-8'))
    except ConnectionError:
        print('Connection lost')
        client_socket.close()
        break

