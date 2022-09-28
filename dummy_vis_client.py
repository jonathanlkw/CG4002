from socket import *

server_name = 'localhost'
server_port = 2021

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((server_name, server_port))

while True:
    try:
        game_data = client_socket.recv(2048)
        print(game_data.decode('utf-8'))
    except ConnectionError:
        print('Connection lost')
        client_socket.close()
        break