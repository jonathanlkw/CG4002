import random
import time
from paho.mqtt import client as mqtt_client
from GameState import GameState
from StateStaff import StateStaff
from Helper import Actions

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

def updateGamestate(p1_state, p2_state, vis_publisher):
    '''
    Function that updates the global game_state and immediately publishes the updated game_state to the broker.
    '''
    global game_state
    game_state.init_players(p1_state, p2_state)
    vis_publisher.publish(game_state)

if __name__ == '__main__':

    player1_state = StateStaff()
    player2_state = StateStaff()
    game_state = GameState()
    game_state.init_players(player1_state, player2_state)
    player1_move = Actions.no
    player2_move = Actions.no
    player1_pos = 1 # arbitrary player 1 position for individual subsystem test (to be replaced with hit/miss flags)
    player2_pos = 2 # arbitrary player 2 position for individual subsystem test (to be replaced with hit/miss flags)

    vis_publisher = VisualizerPublisher()
    vis_publisher.connect_mqtt()
    vis_subcriber = VisualizerSubscriber()
    vis_subcriber.connect_mqtt()
    vis_subcriber.subscribe()
    time.sleep(1)
    while True:
        move_data = input('Enter a move: ')
        player1_move = Actions.all[random.randint(1,4)]
        player1_state.update(True, True, player1_move, player2_move, player2_state.action_is_valid(player2_move))
        player2_move = Actions.all[random.randint(1,4)]
        player2_state.update(True, True, player2_move, player1_move, player1_state.action_is_valid(player1_move))
        updateGamestate(player1_state, player2_state, vis_publisher)
        print(game_state._get_data_plain_text())
        #time.sleep(2)
    

