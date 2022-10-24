from Helper import Actions
import random

def identify_move(ax, ay, az, gx, gy, gz):
    '''
    Function that identifies moves and updates appropriate flags
    '''
    action_list = Actions.all + [Actions.logout]
    #identified_action = Actions.no
    #action_num = int(input("Enter Action Number: "))
    identified_action = action_list[random.randint(2,4)]
    print(identified_action)
    return identified_action
