from socket import *
import sshtunnel

def send_plaintext(remote_socket, msg):
    success = True
    plaintext = msg

    # ice_print_debug(f"Sending message to client: {plaintext} (Unencrypted)")
    # send len followed by '_' followed by cypher
    m = (len(plaintext))+'_'
    try:
        remote_socket.sendall(m.encode("utf-8"))
        remote_socket.sendall(plaintext.encode("utf-8"))
    except OSError:
        print("Connection terminated")
        success = False
    return success

with sshtunnel.open_tunnel(
    ssh_address_or_host=('sunfire.comp.nus.edu.sg', 22),
    remote_bind_address=('192.168.95.243', 22),
    ssh_username='lamkwj',
    ssh_password='CG4002plsworkpls'
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
                #To be replaced with actual packets
                move_data = input('Enter a move: ')
                send_plaintext(client_socket, move_data)
            except ConnectionError:
                print('Connection lost')
                client_socket.close()
                break
            