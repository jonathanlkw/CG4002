import json
from GameState import GameState
from PlayerState import PlayerStateBase
from StateStaff import StateStaff
from Helper import Actions
from socket import *
import traceback
import concurrent.futures
from threading import Lock
import random
from paho.mqtt import client as mqtt_client

KEY = 'PLSPLSPLSPLSWORK'
MAX_CONNECTIONS = 2

# Global variables for storage of game state
game_state = None

player1_state = None
player2_state = None
player1_move = None
player2_move = None
player1_pos = None #Remove
player2_pos = None #Remove
player1_grenade_hit = 0
player2_grenade_hit = 0

program_ended = False
send_to_eval = False
game_state_lock = Lock()

def initializeGamestate():
    global game_state
    global player1_state
    global player2_state
    global player1_move
    global player2_move
    global player1_pos
    global player2_pos

    player1_state = StateStaff()
    player2_state = StateStaff()
    game_state = GameState()
    game_state.init_players(player1_state, player2_state)
    player1_move = Actions.no
    player2_move = Actions.no
    player1_pos = 1 # arbitrary player 1 position for individual subsystem test (to be replaced with hit/miss flags)
    player2_pos = 2 # arbitrary player 2 position for individual subsystem test (to be replaced with hit/miss flags)

def updateGamestate(p1_state, p2_state, vis_publisher):
    '''
    Function that updates the global game_state and immediately publishes the updated game_state to the broker.
    '''
    global game_state
    game_state.init_players(p1_state, p2_state)
    vis_publisher.publish(game_state)
    #print(game_state._get_data_plain_text())

def replaceGamestate(updated_state, vis_publisher):
    '''
    Function that replaces the current game_state with the model game_state from eval_server.
    '''
    global player1_state
    global player2_state
    global send_to_eval
    player1_state.initialize_from_dict(updated_state.get('p1'))
    player2_state.initialize_from_dict(updated_state.get('p2'))
    updateGamestate(player1_state, player2_state, vis_publisher)
    send_to_eval = False

def identifyMove(move_data):
    '''
    Dummy move identification function for testing purposes. If action is not specified specifically, generate random action.
    '''
    for action in Actions.all:
        if move_data == action:
            return action
    return Actions.all[random.randint(1,4)]

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
        global send_to_eval
        data = game_state._get_data_plain_text()
        #p1_action = game_state.get_dict().get("p1").get("action")
        #p2_action = game_state.get_dict().get("p2").get("action")
        #data = "P1 Action: " + p1_action + ", P2 Action: " + p2_action 
        self.vis_publisher.publish(self.topic, data)
        send_to_eval = True # To be replaced with flag that ensures both players actions are updated before sending to eval_server for 2-player game
        
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
            if decoded_msg_list[0] == "P1":
                player1_grenade_hit = int(decoded_msg_list[1].strip())
            elif decoded_msg_list[2] == "P2":
                player2_grenade_hit = int(decoded_msg_list[3].strip())

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
        global player1_pos
        global player2_pos
       
        while True:
            move_data = self.recv_data(connection)
            game_state_lock.acquire()
            if id == 1:
                player1_move = identifyMove(move_data)
                player1_state.update(player1_pos, player2_pos, player1_move, player2_move, player2_state.action_is_valid(player2_move))
                print('Player 1 move: %s' % player1_move)
            else:
                player2_move = identifyMove(move_data)
                player2_state.update(player2_pos, player1_pos, player2_move, player1_move, player1_state.action_is_valid(player1_move))       
                print('Player 2 move: %s' % player2_move)

            updateGamestate(player1_state, player2_state, self.vis_publisher)
            game_state_lock.release()
            
    def setup_connection(self):
        self.relay_server_socket.listen()
        print('Relay Server waiting for connection')

        relay_executor = concurrent.futures.ThreadPoolExecutor(MAX_CONNECTIONS)
        
        for i in range(MAX_CONNECTIONS):
            id = i + 1 
            connection, client_addr = self.relay_server_socket.accept()
            print('Relay %s connected' % str(id))
            relay_executor.submit(self.serve_connection, connection, id)

    def recv_data(self, connection):
        '''
        Function for receiving unencrypted data from relay_client.
        Fbtained and modified from eval_server code.
        '''
        
        relay_data = None
        try:
            # recv length followed by '_' followed by message
            data = b''
            while not data.endswith(b'_'):
                _d = connection.recv(1)
                print(_d)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                self.stop()

            data = data.decode("utf-8")
            print(data)
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
            print(relay_data)
        except ConnectionResetError:
            print('Connection Reset')
            self.stop()
        return relay_data

    def stop(self):
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
    initializeGamestate()

    vis_publisher = VisualizerPublisher()
    vis_publisher.connect_mqtt()
    vis_subcriber = VisualizerSubscriber()
    vis_subcriber.connect_mqtt()
    vis_subcriber.subscribe()

    relay_server = RelayServer(2021, vis_publisher)
    relay_server.setup_connection()

    eval_client = EvalClient('localhost', 2022)
    eval_client.connect()

    while True:
        try:
            if send_to_eval:
                eval_client.send_game_state(game_state)
                updated_state = eval_client.recv_update()
                game_state_lock.acquire()
                replaceGamestate(updated_state, vis_publisher)
                #print(game_state._get_data_plain_text())
                game_state_lock.release()
        except ConnectionError:
            print("Program Ended")
            break
        except KeyboardInterrupt:
            print("Program Ended")
            break

    eval_client.stop()
    relay_server.stop()
    vis_publisher.close()
    vis_subcriber.close()


