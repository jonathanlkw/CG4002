import json
from GameState import GameState
from PlayerState import PlayerStateBase
from StateStaff import StateStaff
from Helper import Actions
from MoveIdentifier2 import identify_move
from MoveIdentifier2 import identify_second_move
from socket import *
import concurrent.futures
import threading
import random
from paho.mqtt import client as mqtt_client
import queue
import sys

KEY = 'PLSPLSPLSPLSWORK'
MAX_CONNECTIONS = 2
EVAL_IP = '0'
EVAL_PORT = 0
RELAY_PORT = 0
IDWINDOW = 75
LONGWINDOW = 0.8
SHORTWINDOW = 0.2
BUFFERWINDOW = 1.5

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
player1_updated_action = 0
player2_updated_action = 0
opp_in_sight_list = [0, 0]
connection_list = [0, 0, 0, 0, 0, 0]

p1_gun_hit_event = threading.Event()
p2_gun_hit_event = threading.Event()
p1_grenade_hit_event = threading.Event()
p2_grenade_hit_event = threading.Event()
p1_updated_action_event = threading.Event()
p2_updated_action_event = threading.Event()
p1_move_id_event = threading.Event()
p2_move_id_event = threading.Event()
update_queue = queue.Queue(1)
p1_move_list = [[],[],[],[],[],[]]
p2_move_list = [[],[],[],[],[],[]]
program_ended = True
game_state_lock = threading.Lock()

def reset_p1_gun_hit(): 
    global p1_gun_hit_event
    def set_to_zero():
        global player1_gun_hit
        player1_gun_hit = 0
    
    while True:
        p1_gun_hit_event.wait()
        t = threading.Timer(LONGWINDOW, set_to_zero)
        t.start()
        print("P1: hit timeout")
        p1_gun_hit_event.clear()

# def reset_p1_grenade_hit(): 
#     global p1_grenade_hit_event
#     def set_to_zero():
#         global player1_grenade_hit
#         player1_grenade_hit = 0
    
#     while True:
#         p1_grenade_hit_event.wait()
#         t = threading.Timer(LONGWINDOW, set_to_zero)
#         t.start()
#         print("P1: grenade hit timeout")
#         p1_grenade_hit_event.clear()

def reset_p2_gun_hit(): 
    global p2_gun_hit_event
    def set_to_zero():
        global player2_gun_hit
        player2_gun_hit = 0
    
    while True:
        p2_gun_hit_event.wait()
        t = threading.Timer(LONGWINDOW, set_to_zero)
        t.start()
        print("P2: hit timeout")
        p2_gun_hit_event.clear()

# def reset_p2_grenade_hit(): 
#     global p2_grenade_hit_event
#     def set_to_zero():
#         global player2_grenade_hit
#         player2_grenade_hit = 0
    
#     while True:
#         p2_grenade_hit_event.wait()
#         t = threading.Timer(LONGWINDOW, set_to_zero)
#         t.start()
#         print("P2: grenade hit timeout")
#         p2_grenade_hit_event.clear()

def reset_p1_updated_event():
    global p1_updated_action_event
    def set_to_zero():
        global player1_updated_action
        player1_updated_action = 0
    
    while True:
        p1_updated_action_event.wait()
        t = threading.Timer(BUFFERWINDOW, set_to_zero)
        t.start()
        p1_updated_action_event.clear()

def reset_p2_updated_event():
    global p2_updated_action_event
    def set_to_zero():
        global player2_updated_action
        player2_updated_action = 0
    
    while True:
        p2_updated_action_event.wait()
        t = threading.Timer(BUFFERWINDOW, set_to_zero)
        t.start()
        p2_updated_action_event.clear()

def p1_handle_id_move(publisher):
    global p1_move_list
    global player1_move
    global player1_updated_action
    global player1_grenade
    global opp_in_sight_list

    while True:
        p1_move_id_event.wait()
        player1_updated_action = 1
        p1_updated_action_event.set()
        player1_move = identify_move(p1_move_list[0], p1_move_list[1], p1_move_list[2], p1_move_list[3], p1_move_list[4], p1_move_list[5])
        p1_move_list = [[],[],[],[],[],[]]
        if player1_move != Actions.no:        
            with game_state_lock:
                player1_state.update(player1_gun_hit, opp_in_sight_list[1], player1_move, Actions.no, player2_state.action_is_valid(Actions.no))
                player2_state.update(player2_gun_hit, opp_in_sight_list[0], Actions.no, player1_move, player1_state.action_is_valid(player1_move)) 
            update_gamestate(player1_state, player2_state, publisher)
            player1_grenade = 0
        else:
            player1_updated_action = 0
        p1_move_id_event.clear()
        print("P1: " + player1_move)
        if (player1_move != Actions.no) and (player2_move != Actions.no):
            update_queue.put(0, True)

def p2_handle_id_move(publisher):
    global p2_move_list
    global player2_move
    global player2_updated_action
    global player2_grenade
    global opp_in_sight_list

    while True:
        p2_move_id_event.wait()
        player2_updated_action = 1
        p2_updated_action_event.set()
        player2_move = identify_second_move(p2_move_list[0], p2_move_list[1], p2_move_list[2], p2_move_list[3], p2_move_list[4], p2_move_list[5])
        p2_move_list = [[],[],[],[],[],[]]
        if player2_move != Actions.no:
            with game_state_lock:
                player1_state.update(player1_gun_hit, opp_in_sight_list[1], Actions.no, player2_move, player2_state.action_is_valid(player2_move))
                player2_state.update(player2_gun_hit, opp_in_sight_list[0], player2_move, Actions.no, player1_state.action_is_valid(Actions.no))
            update_gamestate(player1_state, player2_state, publisher)
            player2_grenade = 0
        else:
            player2_updated_action = 0
        p2_move_id_event.clear()
        print("P2: " + player2_move)
        if (player1_move != Actions.no) and (player2_move != Actions.no):
            update_queue.put(0, True)

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
    with game_state_lock:
        game_state.init_players(p1_state, p2_state)
    print(game_state._get_data_plain_text())
    vis_publisher.publish(game_state._get_data_plain_text())

def replace_gamestate(updated_state, vis_publisher):
    '''
    Function that replaces the current game_state with the model game_state from eval_server.
    '''
    global player1_state
    global player2_state
    global player1_move
    global player2_move
    if (player1_move != Actions.shield and updated_state.get('p1').get('action') == Actions.shield):
        with game_state_lock:
            player1_state.initialize_from_dict_eval_invalid_shield(updated_state.get('p1'))
    else:
        with game_state_lock:
            player1_state.initialize_from_dict_eval(updated_state.get('p1'))
    if (player2_move != Actions.shield and updated_state.get('p2').get('action') == Actions.shield):
        with game_state_lock:
            player2_state.initialize_from_dict_eval_invalid_shield(updated_state.get('p2'))
    else:
        with game_state_lock:
            player2_state.initialize_from_dict_eval(updated_state.get('p2'))
    player1_move = Actions.no
    player2_move = Actions.no
    update_gamestate(player1_state, player2_state, vis_publisher)

def make_connectivity_message(player_id, beetle_number, connection_status):
    player_list = ["P1: ", "P2: "]
    beetle_list = ["glove-", "gun-", "belt-", "glove-", "gun-", "belt-"]
    connection_list = ["disconnected", "connected"]
    return player_list[player_id-1] + beetle_list[beetle_number] + connection_list[connection_status]

def parse_packets(move_data, publisher): 
    '''
        IMU IRt IRr Connect
    P1   0   1   2    6
    P2   3   4   5    7
    '''
    global player1_state
    global player2_state
    global player1_move
    global player2_move
    global player1_shoot
    global player2_shoot
    global player1_gun_hit
    global player2_gun_hit
    global player1_grenade
    global player2_grenade
    global player1_updated_action
    global player2_updated_action
    global opp_in_sight_list
    global connection_list
    global p1_move_list
    global p2_move_list
    global program_ended

    packet_list = move_data.split("_")
    packet_type = int(packet_list[0])

    if (packet_type == 6 or packet_type == 7):
        connection_list[int(packet_list[1])] = int(packet_list[2])
        connection_message = make_connectivity_message(int(packet_list[0])-5, int(packet_list[1]), int(packet_list[2]))
        publisher.publish(connection_message)
        print(connection_message)
    elif not program_ended:
        if packet_type == 0:
            for i in range(6):
                if not player1_updated_action:
                    p1_move_list[i] += [int(packet_list[i+1])]          
            if (len(p1_move_list[5]) >= IDWINDOW and not player1_updated_action):   
                # player1_move = identify_move(p1_move_list[0], p1_move_list[1], p1_move_list[2], p1_move_list[3], p1_move_list[4], p1_move_list[5])
                # p1_move_list = [[],[],[],[],[],[]]
                # if player1_move != Actions.no:
                #     player1_updated_action = 1
                #     p1_updated_action_event.set()
                #     if player1_move == Actions.grenade:
                #         p2_grenade_hit_event.wait(HITWINDOW)
                #     with game_state_lock:
                #         player1_state.update(player1_gun_hit, player1_grenade_hit, player1_move, Actions.no, player2_state.action_is_valid(Actions.no))
                #         player2_state.update(player2_gun_hit, player2_grenade_hit, Actions.no, player1_move, player1_state.action_is_valid(player1_move)) 
                #     update_gamestate(player1_state, player2_state, publisher)
                #     player1_grenade = 0
                #     player2_grenade_hit = 0
                #     p2_grenade_hit_event.clear()
                # print("P1: " + player1_move)
                # if (player1_move != Actions.no) and (player2_move != Actions.no):
                #     update_queue.put(0, True) 
                p1_move_id_event.set()  
        elif packet_type == 1:
            print("P1: " + player1_move)
            player1_shoot = 1
            player1_move = Actions.shoot
            p2_gun_hit_event.wait(SHORTWINDOW)
            print("P1: shoot window closed")
            with game_state_lock:
                player1_state.update(player1_gun_hit, opp_in_sight_list[1], player1_move, Actions.no, player2_state.action_is_valid(Actions.no))
                player2_state.update(player2_gun_hit, opp_in_sight_list[0], Actions.no, player1_move, player1_state.action_is_valid(player1_move))
            update_gamestate(player1_state, player2_state, publisher)
            player1_shoot = 0
            player2_gun_hit = 0
            #print("P1: " + player1_move)
            p2_gun_hit_event.clear()
            if (player1_move != Actions.no) and (player2_move != Actions.no):
                update_queue.put(0, True)
        elif packet_type == 2:
            player1_gun_hit = 1
            print("P1: hit")
            p1_gun_hit_event.set()
        elif packet_type == 3:
            for i in range(6):
                if not player2_updated_action:
                    p2_move_list[i] += [int(packet_list[i+1])]
            if (len(p2_move_list[5]) >= IDWINDOW and not player2_updated_action):
                # player2_move = identify_second_move(p2_move_list[0], p2_move_list[1], p2_move_list[2], p2_move_list[3], p2_move_list[4], p2_move_list[5])
                # p2_move_list = [[],[],[],[],[],[]]
                # if player2_move != Actions.no: 
                #     player2_updated_action = 1
                #     p2_updated_action_event.set()
                #     if player2_move == Actions.grenade:
                #         p1_grenade_hit_event.wait(HITWINDOW)
                #     with game_state_lock:
                #         player1_state.update(player1_gun_hit, player1_grenade_hit, Actions.no, player2_move, player2_state.action_is_valid(player2_move))
                #         player2_state.update(player2_gun_hit, player2_grenade_hit, player2_move, Actions.no, player1_state.action_is_valid(Actions.no))
                #     update_gamestate(player1_state, player2_state, publisher)
                #     player2_grenade = 0
                #     player1_grenade_hit = 0
                #     p1_grenade_hit_event.clear()
                # print("P2: " + player2_move)
                # if (player1_move != Actions.no) and (player2_move != Actions.no):
                #     update_queue.put(0, True) #2P EVAL
                p2_move_id_event.set()
        elif packet_type == 4:
            print("P2: " + player2_move)
            player2_shoot = 1
            player2_move = Actions.shoot
            p1_gun_hit_event.wait(SHORTWINDOW)
            print("P2: shoot window closed")
            with game_state_lock:
                player1_state.update(player1_gun_hit, opp_in_sight_list[1], Actions.no, player2_move, player2_state.action_is_valid(player2_move))
                player2_state.update(player2_gun_hit, opp_in_sight_list[0], player2_move, Actions.no, player1_state.action_is_valid(Actions.no))
            update_gamestate(player1_state, player2_state, publisher)
            player2_shoot = 0
            player1_gun_hit = 0
            #print("P2: " + player2_move)
            p1_gun_hit_event.clear()
            if (player1_move != Actions.no) and (player2_move != Actions.no):
                update_queue.put(0, True)
        elif packet_type == 5:
            player2_gun_hit = 1
            print("P2: hit")
            p2_gun_hit_event.set()
        

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
        
    def publish(self, data):
        '''
        Function that publishes game_state and other messages to self.topic
        '''
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
            global opp_in_sight_list
            decoded_msg = msg.payload.decode()
            print(f"Received `{decoded_msg}` from `{msg.topic}` topic")
            decoded_msg_list = decoded_msg.split(":")
            if decoded_msg_list[0] == "P1":
                opp_in_sight_list[0] = int(decoded_msg_list[1].strip())
            elif decoded_msg_list[0] == "P2":
                opp_in_sight_list[1] = int(decoded_msg_list[1].strip())

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

    def serve_connection(self, connection):
        '''
        Function that continuously receives data from relay_client and updates the global game_state.
        '''
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
            self.relay_executor.submit(self.serve_connection, connection)

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
        #print("-----RECEIVED DATA-----")
        #print(relay_data) #DEBUG!!
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
        print("Eval Client connected!")
        
    def send_game_state(self, gamestate):
        success = gamestate.send_encrypted_text(self.client_socket, KEY)
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
    if len(sys.argv) < 3:
        print('Invalid number of arguments')
        sys.exit()
    EVAL_IP = sys.argv[1]
    EVAL_PORT = int(sys.argv[2])
    RELAY_PORT = int(sys.argv[3])

    initialize_gamestate()

    eval_client = EvalClient(EVAL_IP, EVAL_PORT)
    eval_client.connect()

    vis_publisher = VisualizerPublisher()
    vis_publisher.connect_mqtt()
    vis_subcriber = VisualizerSubscriber()
    vis_subcriber.connect_mqtt()
    vis_subcriber.subscribe()

    relay_server = RelayServer(RELAY_PORT, vis_publisher)
    relay_server.setup_connection()

    p1_hit_thread = threading.Thread(target = reset_p1_gun_hit, daemon = True)
    p2_hit_thread = threading.Thread(target = reset_p2_gun_hit, daemon = True)
    #p1_grenade_hit_thread = threading.Thread(target = reset_p1_grenade_hit, daemon = True)
    #p2_grenade_hit_thread = threading.Thread(target = reset_p2_grenade_hit, daemon = True)
    p1_updated_action_thread = threading.Thread(target = reset_p1_updated_event, daemon = True)
    p2_updated_action_thread = threading.Thread(target = reset_p2_updated_event, daemon = True)
    p1_move_id_thread = threading.Thread(target = p1_handle_id_move, args = (vis_publisher,), daemon = True)
    p2_move_id_thread = threading.Thread(target = p2_handle_id_move, args = (vis_publisher,), daemon = True)

    p1_hit_thread.start()
    p2_hit_thread.start()
    #p1_grenade_hit_thread.start()
    #p2_grenade_hit_thread.start()
    p1_updated_action_thread.start()
    p2_updated_action_thread.start()
    p1_move_id_thread.start()
    p2_move_id_thread.start()

    _ = input("Press enter to start:")
    print("Game starting...")
    resend_command = 'y'
    while resend_command == 'y':
        vis_publisher.publish("Start")
        print("Start")
        for i in range (6):
            if i < 3:
                connection_message = make_connectivity_message(1, i, connection_list[i])
                vis_publisher.publish(connection_message)
            else:
                connection_message = make_connectivity_message(2, i, connection_list[i])
                vis_publisher.publish(connection_message)
            print(connection_message)
        resend_command = input("Resend start command? ")
    program_ended = False
    print("Game started!")

    while not program_ended:
        update_queue.get(True)
        p1_eval_state = StateStaff()
        p2_eval_state = StateStaff()
        eval_game_state = GameState()
        p1_eval_state.initialize_from_player_state_eval(player1_state, player1_move)
        p2_eval_state.initialize_from_player_state_eval(player2_state, player2_move)
        eval_game_state.init_players(p1_eval_state, p2_eval_state)
        print(eval_game_state._get_data_plain_text())
        eval_client.send_game_state(eval_game_state)
        if (player1_move == Actions.logout and player2_move == Actions.logout):
            program_ended = True
        updated_state = eval_client.recv_update()
        replace_gamestate(updated_state, vis_publisher)
    
    print("Program Ended")
    eval_client.stop()
    relay_server.stop()
    vis_publisher.close()
    vis_subcriber.close()
    
    



