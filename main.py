import json
from GameState import GameState
from PlayerState import PlayerStateBase
from StateStaff import StateStaff
from Helper import Actions
from socket import *
import traceback
import concurrent.futures
import threading
import random
from paho.mqtt import client as mqtt_client
import queue
import time

KEY = 'PLSPLSPLSPLSWORK'
MAX_CONNECTIONS = 2
EVAL_IP = 'localhost'
IDWINDOW = 10
HITWINDOW = 0.1

#Global variables for storage of game state
game_state = None

player1_state = None
player2_state = None
player1_move = None
player2_move = None
player1_shoot = 0
player2_shoot = 0
player1_gun_hit = 0
player2_gun_hit = 0
player1_grenade = 0
player2_grenade = 0
player1_grenade_hit = 0
player2_grenade_hit = 0

hit_time_start = 0
hit2_time_start = 0
grenade_time_start = 0
grenade2_time_start = 0
update_queue = queue.Queue(1)
p1_move_list = [[],[],[],[],[],[]]
p2_move_list = [[],[],[],[],[],[]]
program_ended = False
game_state_lock = threading.Lock()

def print_flags():
    '''
    Function that prints all the game_state flags for checking purposes.
    To be deleted.
    '''
    global player1_move
    global player2_move
    global player1_shoot
    global player2_shoot
    global player1_gun_hit
    global player2_gun_hit
    global player1_grenade
    global player2_grenade
    global player1_grenade_hit
    global player2_grenade_hit 
    print("P1 move: " + player1_move)
    print("P2 move: " + player2_move)
    print("P1 shoot: " + player1_shoot)
    print("P2 shoot: " + player2_shoot)
    print("P1 hit: " + player1_gun_hit)
    print("P2 hit: " + player2_gun_hit)
    print("P1 grenade: " + player1_grenade)
    print("P2 grenade: " + player2_grenade)
    print("P1 grenade hit: " + player1_grenade_hit)
    print("P2 grenade hit: " + player2_grenade_hit)


def initialize_gamestate():
    '''
    Function that sets all game stats to the starting values.
    '''
    global game_state
    global player1_state
    global player2_state
    global player1_move
    global player2_move

    player1_state = StateStaff()
    player2_state = StateStaff()
    game_state = GameState()
    game_state.init_players(player1_state, player2_state)
    player1_move = Actions.no
    player2_move = Actions.no

def update_gamestate(p1_state, p2_state, vis_publisher):
    '''
    Function that updates the global game_state and immediately publishes the updated game_state to the broker.
    '''
    global game_state
    game_state_lock.acquire()
    game_state.init_players(p1_state, p2_state)
    game_state_lock.release()
    vis_publisher.publish(game_state)

def replace_gamestate(updated_state, vis_publisher):
    '''
    Function that replaces the current game_state with the model game_state from eval_server.
    '''
    global player1_state
    global player2_state
    player1_state.initialize_from_dict(updated_state.get('p1'))
    player2_state.initialize_from_dict(updated_state.get('p2'))
    update_gamestate(player1_state, player2_state, vis_publisher)

def parse_packets(move_data, publisher): #TO BE EDITED
    '''
    IMU IRt IRr
    P1 0 1 2 
    P2 3 4 5
    '''
    global player1_move
    global player2_move
    global player1_shoot
    global player2_shoot
    global player1_gun_hit
    global player2_gun_hit
    global player1_grenade
    global player2_grenade
    global p1_move_list
    global p2_move_list
    global hit_time_start
    global hit2_time_start
    global grenade_time_start
    global grenade2_time_start

    packet_list = move_data.split("_")
    packet_type = int(packet_list[0])
    if packet_type == 0:
        for i in range(6):
            p1_move_list[i] += [int(packet_list[i+1])]
            print(p1_move_list)
        if len(p1_move_list[5]) >= IDWINDOW:
            player1_move = identify_move(p1_move_list[0], p1_move_list[1], p1_move_list[2], p1_move_list[3], p1_move_list[4], p1_move_list[5])
            if player1_move == Actions.grenade:
                current_time = time.time()
                if (grenade_time_start != 0):
                    if (current_time - grenade_time_start >= HITWINDOW):
                        p1_move_list = [[],[],[],[],[],[]]
                        update_gamestate(player1_state, player2_state, publisher)
                        grenade_time_start = 0
                        update_queue.put(0, True)
                else:
                    grenade_time_start = time.time()
            else:
                p1_move_list = [[],[],[],[],[],[]]
                update_gamestate(player1_state, player2_state, publisher)
                update_queue.put(0, True)
    elif packet_type == 1:
        player1_shoot = 1
        player1_move = Actions.shoot
        current_time = time.time()
        if (hit_time_start != 0):
            if (current_time - hit_time_start >= HITWINDOW):
                update_gamestate(player1_state, player2_state, publisher)
                hit_time_start = 0
                update_queue.put(0, True)
        else:
            hit_time_start = time.time()
    elif packet_type == 2:
        player1_gun_hit = 1
    elif packet_type == 3:
        for i in range(6):
            p2_move_list[i] += [int(packet_list[i+1])]
            print(p2_move_list)
        if len(p2_move_list[5]) >= IDWINDOW:
            player2_move = identify_move(p2_move_list[0], p2_move_list[1], p2_move_list[2], p2_move_list[3], p2_move_list[4], p2_move_list[5])
            if player2_move == Actions.grenade:
                current_time = time.time()
                if (grenade2_time_start != 0):
                    if (current_time - grenade2_time_start >= HITWINDOW):
                        p2_move_list = [[],[],[],[],[],[]]
                        update_gamestate(player1_state, player2_state, publisher)
                        grenade2_time_start = 0
                        update_queue.put(0, True)
                else:
                    grenade2_time_start = time.time()
            else:
                p2_move_list = [[],[],[],[],[],[]]
                update_gamestate(player1_state, player2_state, publisher)
                update_queue.put(0, True)
    elif packet_type == 4:
        player2_shoot = 1
        player2_move = Actions.shoot
        current_time = time.time()
        if (hit2_time_start != 0):
            if (current_time - hit2_time_start >= HITWINDOW):
                update_gamestate(player1_state, player2_state, publisher)
                hit2_time_start = 0
                update_queue.put(0, True)
        else:
            hit2_time_start = time.time()
        update_gamestate(player1_state, player2_state, publisher)
        update_queue.put(0, True)
    elif packet_type == 5:
        player2_gun_hit = 1

def identify_move(ax, ay, az, gx, gy, gz):
    '''
    Function that identifies moves and updates appropriate flags
    '''
    identified_action = Actions.all[random.randint(2,4)] 
    return identified_action

class VisualizerPublisher:
    def __init__(self):
        self.broker = 'test.mosquitto.org'
        self.port = 1883
        self.topic = "CG4002B19"
        # generate client ID with pub prefix randomly
        self.client_id = f'python-mqtt-{random.randint(0, 1000)}'
        self.username = 'lamkwj'
        self.password = 'helloworld'
        print("Visualizer Publisher waiting for connection")

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Visualizer Publisher connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        self.vis_publisher = mqtt_client.Client(self.client_id)
        self.vis_publisher.username_pw_set(self.username, self.password)
        self.vis_publisher.on_connect = on_connect # uncalled due to no loop_start()
        self.vis_publisher.connect(self.broker, self.port)
        print("Visualizer Publisher connected to MQTT Broker!")
        
    def publish(self, game_state):
        '''
        Function that publishes game_state to self.topic
        '''
        data = game_state._get_data_plain_text()
        #p1_action = game_state.get_dict().get("p1").get("action")
        #p2_action = game_state.get_dict().get("p2").get("action")
        #data = "P1 Action: " + p1_action + ", P2 Action: " + p2_action 
        self.vis_publisher.publish(self.topic, data)
        
    def close(self):
        self.vis_publisher.disconnect()

class VisualizerSubscriber:
    def __init__(self):
        self.broker = 'test.mosquitto.org'
        self.port = 1883
        self.topic = "CG4002B19_Reply"
        # generate client ID with pub prefix randomly
        self.client_id = f'python-mqtt-{random.randint(0, 1000)}'
        self.username = 'lamkwj'
        self.password = 'helloworld'
        print("Visualizer Subscriber waiting for connection")

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Visualizer Subscriber connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        self.vis_subscriber = mqtt_client.Client(self.client_id)
        self.vis_subscriber.username_pw_set(self.username, self.password)
        self.vis_subscriber.on_connect = on_connect
        self.vis_subscriber.connect(self.broker, self.port)
    
    def subscribe(self):
        def on_message(client, userdata, msg):
            global player1_grenade_hit
            global player2_grenade_hit
            decoded_msg = msg.payload.decode()
            print(f"Received `{decoded_msg}` from `{msg.topic}` topic")
            decoded_msg_list = decoded_msg.split(":")
            #UPDATE CODE HERE FOR VISUALIZER FORMAT
            if decoded_msg_list[0] == "P1":
                player1_grenade_hit = int(decoded_msg_list[1].strip())
            elif decoded_msg_list[0] == "P2":
                player2_grenade_hit = int(decoded_msg_list[1].strip())

        self.vis_subscriber.subscribe(self.topic)
        self.vis_subscriber.on_message = on_message
        self.vis_subscriber.loop_start()
    
    def close(self):
        self.vis_subscriber.loop_stop()
        self.vis_subscriber.disconnect()

class RelayServer:
    def __init__(self, server_port, vis_publisher):
        self.relay_server_socket = socket(AF_INET, SOCK_STREAM)
        self.relay_server_addr = ('', server_port)
        print('Relay Server starting up on %s port %s' % self.relay_server_addr)
        self.relay_server_socket.bind(self.relay_server_addr)
        self.vis_publisher = vis_publisher

    def serve_connection(self, connection, id):
        '''
        Function that continuously receives data from relay_client and updates the global game_state.
        '''
        #global game_state
        global player1_state
        global player2_state
        global player1_move
        global player2_move
        global player1_gun_hit
        global player2_gun_hit
        global player1_grenade_hit
        global player2_grenade_hit

        while True:
            move_data = self.recv_data(connection)
            parse_packets(move_data, self.vis_publisher)
            
    def setup_connection(self):
        self.relay_server_socket.listen()
        print('Relay Server waiting for connection')

        self.relay_executor = concurrent.futures.ThreadPoolExecutor(MAX_CONNECTIONS)
        
        for i in range(MAX_CONNECTIONS):
            id = i + 1 
            connection, client_addr = self.relay_server_socket.accept()
            print('Relay %s connected' % str(id))
            self.relay_executor.submit(self.serve_connection, connection, id)

    def recv_data(self, connection):
        '''
        Function for receiving unencrypted data from relay_client.
        Obtained and modified from eval_server code.
        '''
        
        relay_data = None
        try:
            # recv length followed by '_' followed by message
            data = b''
            while not data.endswith(b'_'):
                _d = connection.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                self.stop()

            data = data.decode("utf-8")
            length = int(data[:-1])

            data = b''
            while len(data) < length:
                _d = connection.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from the client')
                self.stop()
            relay_data = data.decode("utf8")  # Decode raw bytes to UTF-8
        except ConnectionResetError:
            print('Connection Reset')
            self.stop()
        return relay_data

    def stop(self):
        self.relay_executor.shutdown()
        self.relay_server_socket.close()


class EvalClient:
    def __init__(self, server_name, server_port):
        self.server_name = server_name
        self.server_port = server_port
        self.client_socket = None

    def connect(self):
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((self.server_name, self.server_port))
        self.client_socket = client_socket
        
    def send_game_state(self, GameState: game_state):
        success = game_state.send_encrypted_text(self.client_socket, KEY)
        return success

    def recv_update(self):
        '''
        Function for receiving unencrypted messages from eval_server.
        Obtained and modified from eval_server code.
        '''
        game_state_received = None
        try:
            # recv length followed by '_' followed by message
            data = b''
            while not data.endswith(b'_'):
                _d = self.client_socket.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                self.stop()

            data = data.decode("utf-8")
            length = int(data[:-1])

            data = b''
            while len(data) < length:
                _d = self.client_socket.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from the client')
                self.stop()
            game_state_received = data.decode("utf8")  # Decode raw bytes to UTF-8
        except ConnectionResetError:
            print('Connection Reset')
            self.stop()
        return json.loads(game_state_received)

    def stop(self):
        try:
            self.client_socket.close()
        except OSError:
            pass

if __name__ == '__main__':
    initialize_gamestate()

    vis_publisher = VisualizerPublisher()
    vis_publisher.connect_mqtt()
    vis_subcriber = VisualizerSubscriber()
    vis_subcriber.connect_mqtt()
    vis_subcriber.subscribe()

    relay_server = RelayServer(2021, vis_publisher)
    relay_server.setup_connection()

    eval_client = EvalClient(EVAL_IP, 2022)
    eval_client.connect()

    while True:
        end = update_queue.get(True)
        eval_client.send_game_state(game_state)
        updated_state = eval_client.recv_update()
        replace_gamestate(updated_state, vis_publisher)
        if end:
            break
    
    eval_client.stop()
    relay_server.stop()
    vis_publisher.close()
    vis_subcriber.close()
    



