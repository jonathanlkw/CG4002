from socket import *
import random
import time

IDWINDOW = 75

server_name = 'localhost'
server_port = 2021

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((server_name, server_port))

def send_plaintext(remote_socket, msg):
    success = True
    plaintext = msg

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
        #user_input = input('Enter a move: ')
        #if (int(user_input) >= 0) and (int(user_input) <= 5):
        #    packet_type = int(user_input)
        #else:
        #    packet_type = random.randint(0,5)
        
        time.sleep(random.uniform(0.1, 0.5))
        packet_type = random.randint(0,5)

        if (packet_type == 0) or (packet_type == 3):
            for i in range (IDWINDOW):
                move_data = str(packet_type) + '_' + str(random.randint(-1000,1000)) + '_' + str(random.randint(-1000,1000)) + '_' + str(random.randint(-1000,1000)) \
                + '_' + str(random.randint(-1000,1000)) + '_' + str(random.randint(-1000,1000)) + '_' + str(random.randint(-1000,1000))
                send_plaintext(client_socket, move_data)
        else: 
            move_data = str(packet_type) + '_' + str(1)
            send_plaintext(client_socket, move_data)
    except ConnectionError:
        print('Connection lost')
        client_socket.close()
        break

