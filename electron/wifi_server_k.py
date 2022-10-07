import socket
import picar_4wd as fc
import sys
import tty
import termios
import asyncio
import time
import json
from enum import Enum


HOST = "192.168.68.106" # IP address of your Raspberry PI
PORT = 65432          # Port to listen on (non-privileged ports are > 1023)

speed = 5
turn_left_timer = 1
turn_right_timer = 1.07
distance_counter = 0
forward_timer = 0
car_position = [24, 10]

class DrivingDirection (Enum):
    towards_destination = 1
    right = 2
    left = 3
    away_from_destination = 4

direction = DrivingDirection.towards_destination

def message_to_frontend():
    car_data=fc.utils.pi_read()
    car_data["direction"]=DrivingDirection(direction).name
    car_data["speed"]=speed
    return json.dumps(car_data)


def turn(turning_direction):

    global distance_counter
    global driver

    if turning_direction == 'right':
        fc.turn_right(speed)
        time.sleep(turn_right_timer)
    else:
        fc.turn_left(speed)
        time.sleep(turn_left_timer)
    fc.stop()
    distance_counter = 0
    return

def updatePositionMovingForward(distance):
    global direction
    global car_position
    print("updating position")
    if direction == DrivingDirection.towards_destination:
        car_position[0] = car_position[0] - distance
        print("222")
    elif direction == DrivingDirection.right:
        car_position[1] = car_position[1] + distance
        print("3333")
    elif direction == DrivingDirection.left:
        car_position[1] = car_position[1] - distance
        print("4444")
    else:
        car_position[0] = car_position[0] + distance
        print("5555")
        
    return

def move_forward():
    global distance_counter
    fc.forward(speed)
    distance_counter += 1
    updatePositionMovingForward(1)
    return

def move_backward():
    global distance_counter
    fc.backward(speed)
    distance_counter += 1
    updatePositionMovingForward(-1)
    return

def check_scan(scan_list, blocked_state):
    if scan_list[0:3] != [ 2, 2, 2]:
        blocked_state['left'] = True
    else:
        blocked_state['left'] = False

    if scan_list[3:7] != [2, 2, 2, 2]:
        blocked_state['centre'] = True
    else:
        blocked_state['centre'] = False

    if scan_list[7:10] != [2, 2, 2]:
        blocked_state['right'] = True
    else:
        blocked_state['right'] = False
    return blocked_state

def decide_on_action(go):
    global direction
    print(direction)
    if go=="forward":
        print("Going Forward") 
        direction = DrivingDirection.towards_destination
        move_forward()
        return

    elif go=="right":
        print("Going Right") 
        direction = DrivingDirection.right
        turn('right')
        return

    elif go=="left":
        print("Going Left") 
        direction = DrivingDirection.left
        turn('left')
        return

    elif go=="backward":
        print("Going Reversed") 
        direction = DrivingDirection.away_from_destination
        move_backward()
        return

    elif go=="stop":
        fc.stop()
        return    


def main():

    blocked_state = {
        'left': False,
        'centre': False,
        'right': False
    }

    encoding='utf-8'

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        try:
            while 1:
                                
                client, clientInfo = s.accept()
                print("server recv from: ", clientInfo)
                data = client.recv(1024) 
                go=data.decode(encoding)

                print("Action: "+go) 
                if data != b"": 
                    decide_on_action(go) 
                    print("Data: ")
                    message=message_to_frontend()
                    encoded_message=bytes(message,encoding)   
                    print(message)
                    client.sendall(encoded_message)
        except: 
            print("Closing socket")
            client.close()
            s.close()

if __name__ == "__main__":

    try: 
        main()
    finally: 
        fc.stop()