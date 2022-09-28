from socket import *
import sshtunnel

with sshtunnel.open_tunnel(
    ssh_address_or_host=('sunfire.comp.nus.edu.sg', 22),
    remote_bind_address=('192.168.95.243', 22),
    ssh_username='lamkwj',
    ssh_password='' #TO BE FILLED
) as tunnel1:
    print('Connection to tunnel1 OK...')
    with sshtunnel.open_tunnel(
        ssh_address_or_host=('localhost', tunnel1.local_bind_port),
        remote_bind_address=('localhost', 2021),
        ssh_username='xilinx',
        ssh_password='xilinx',
    ) as tunnel2:
        print('Connection to tunnel2 OK...')
            
        server_name = 'localhost'
        server_port = tunnel2.local_bind_port

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
            