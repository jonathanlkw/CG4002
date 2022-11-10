from Helper import Actions
import random
import time

def identify_move(ax, ay, az, gx, gy, gz):
    '''
    Function that identifies moves and updates appropriate flags
    '''
    #time.sleep(random.uniform(3.0, 6.0))
    action_list = Actions.all + [Actions.logout]
    #identified_action = Actions.no
    action_num = int(input("P1 Enter Action Number: "))
    identified_action = action_list[action_num]
    #identified_action = action_list[random.randint(0,4)]
    #print(identified_action)
    return identified_action

def identify_second_move(ax, ay, az, gx, gy, gz):
    '''
    Function that identifies moves and updates appropriate flags
    '''
    #time.sleep(random.uniform(3.0, 6.0))
    action_list = Actions.all + [Actions.logout]
    #identified_action = Actions.no
    action_num = int(input("P2 Enter Action Number: "))
    identified_action = action_list[action_num]
    #identified_action = action_list[random.randint(0,4)]
    #print(identified_action)
    return identified_action
