from socket import *
import concurrent.futures
import logging

server_port = 2021
program_ended = False
MAX_CONNECTIONS = 2

server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(('', server_port))
server_socket.listen()
print('Server is ready to connect')

def serve_connection(client, addr):
    while True:
        message = client.recv(2048)
        client.send(message)
        if message.decode() == 'close':
            break

if __name__ == "__main__":
    #format = "%(asctime)s: %(message)s"
    #logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    executor = concurrent.futures.ThreadPoolExecutor(MAX_CONNECTIONS)

    while not program_ended:  
        connection_socket, client_addr = server_socket.accept()
        executor.submit(serve_connection, connection_socket, client_addr)
        
    server_socket.close()
    

    

