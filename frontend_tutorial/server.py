import socket
import sys
import time
import json
import threading
import cv2
import bluetooth
from threading import Thread
from enum import Enum

# Needed to find picar_4wd module
sys.path.insert(0, '/home/pi/picar-4wd/')
import picar_4wd as fc


####################################################################
#  
#           Parameter initialisation
#
####################################################################

# Bluetooth Universally Unique ID to identify Bluetooth service
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

# IP address and port (update as needed)
HOST = "192.168.1.221" # IP address of your Raspberry PI
PORT = 65432          # Port to listen on (non-privileged ports are > 1023)

# Define enum for holding driving direction, in relation to the initial driving direction when the 
# car started.
class DrivingDirection (Enum):
    forwards = 1
    right = 2
    left = 3
    backwards = 4

# Set starting direction of car as toward destination
direction = DrivingDirection.forwards

# Set speed of car
speed = 20

# Initialise distance counter, measured in number of seconds of travel * speed (approximately cms)
distance = 0

# Car moving status, so we know when distance updates are needed
is_car_moving = False

# Use bluetooth variable. When 'true' server connects via bluetooth, otherwise wifi is used
use_bluetooth = True

# Keyboard control mapping from keys to directions (when using bluetooth)
bt_car_controls = {
    'w': 'forward',
    'a': 'left',
    's': 'backward',
    'd': 'right',
    'x': 'stop',
}

# Set timer for calculating distance
timer = time.time()

# Signal to synchronize quitting with multi threads and other host
should_quit = False


####################################################################
#  
#           Car actions
#
####################################################################

# Act on the requested action received from the client
def car_control(action):
    global speed

    # Threading used so input is not blocked while car action is being taken
    action_thread = Thread()

    # Give the thread the respective target function based on requested action
    if action=='forward':
        action_thread = Thread(target=move_forward)
    elif action=='left':
        action_thread = Thread(target=turn, args=(action,))
    elif action=='backward':
        action_thread = Thread(target=move_backward)
    elif action=='right':
        action_thread = Thread(target=turn, args=(action,))
    else:
        stop()
        return

    # Start thread with relevant function
    action_thread.start()

    # Join threads when finnishing
    action_thread.join()


# Execute turn of car
def turn(turning_direction):
    global is_car_moving
    if is_car_moving :
        updateDistance()
        is_car_moving = False
    
    # Set time for turning action for a period in seconds which gives a 90 degree turn angle.
    # Different timers needed for left and right turns to maintain consistent turning angle
    turn_left_timer = 1.3
    turn_right_timer = 1.3

    # Execute turn in direction received in function call and wait for specific time 
    # before stopping
    if turning_direction == 'right':
        fc.turn_right(speed)
        time.sleep(turn_right_timer)

    else:
        fc.turn_left(speed)
        time.sleep(turn_left_timer)
    
    # Stop turn
    fc.stop()
    updateDirection(turning_direction)
    return

# Move car forward and update distance counter each time function is called
def move_forward():
    global is_car_moving
    global timer
    if is_car_moving :
        updateDistance()
    timer = time.time()
    is_car_moving = True
    fc.forward(speed)
    return

# Move car backward and update distance counter each time function is called
def move_backward():
    global is_car_moving
    global timer
    if is_car_moving:
        updateDistance()
    timer = time.time()
    is_car_moving = True
    fc.backward(speed)
    return

def stop():
    global is_car_moving
    if is_car_moving:
        updateDistance()
        is_car_moving = False
    fc.stop()
    return


def updateDistance() :
    global distance
    global timer
    
    # Moved time calculated 
    currentTime = time.time()
    movedTime = currentTime - timer

    # Distance estimated
    distance = distance + round((speed * movedTime))
    return

# Update direction in relation to the initial driving direction of the car
def updateDirection(turn):

    # Use global variable
    global direction

    # Update direction depending on current direction and turning direction
    if direction == DrivingDirection.forwards:

        if turn == 'left':
            direction = DrivingDirection.left
        else :
            direction = DrivingDirection.right

    elif direction == DrivingDirection.right:

        if turn == 'left':
            direction = DrivingDirection.forwards
        else :
            direction = DrivingDirection.backwards

    elif direction == DrivingDirection.left:

        if turn == 'left':
            direction = DrivingDirection.backwards
        else :
            direction = DrivingDirection.forwards

    elif direction == DrivingDirection.backwards:

        if turn == 'left':
            direction = DrivingDirection.right
        else :
            direction = DrivingDirection.left

    else:
        return 


####################################################################
#  
#           Parameter preparation
#
####################################################################

# Prepare parameters to be sent to the client
def prepare_parameters():
    global is_car_moving
    global speed

    # Initiate parameter dictionary with the parameters from the utils function
    parameters = fc.utils.pi_read()
    print("Direction " + DrivingDirection(direction).name)
    parameters["direction"] =  str(DrivingDirection(direction).name)
    print("Is car moving " + str(is_car_moving))
    if (is_car_moving) :
        print("Car is moving and speed is " + str(speed))
        parameters["speed"] = speed
    else :
        parameters["speed"] = 0
                        
    parameters["distance"] = distance
    return json.dumps(parameters)


####################################################################
#  
#           Bluetooth communication
#
####################################################################

# Initiate bluetooth server
def start_server():
    global should_quit
    print("Starting bluetooth server")
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)

    port = server_sock.getsockname()[1]

    bluetooth.advertise_service(server_sock, "CarServer", service_id=uuid,
                                service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE],
                                )

    print("Waiting for connection on RFCOMM channel", port)
    client_sock, client_info = server_sock.accept()
    print("Accepted connection from", client_info)

    try:
        # Open persistence while loop checking for data from the client
        while not should_quit:
            data = client_sock.recv(1024)
            if not data:
                print("Received empty buffer. Server exiting.")
                break
            if data.decode('UTF-8') == "q":
                print("Received q. Setting stop signal.")
                should_quit = True
                break

            print("Received data via bluetooth", data)
            car_control_char = data.decode("UTF-8") 

            # Take relevant action received from client
            if car_control_char:
                action = ''
                if car_control_char in bt_car_controls.keys():
                    action = bt_car_controls[car_control_char]
                    car_control(action)
            
    except OSError as error:
        print("Problem with bluetooth server: " + error)

    print("Disconnecting")
    client_sock.close()
    server_sock.close()
    print("All done.")

# Start bluetooth client for sending data to front end
def start_client():
    global should_quit
    print("Starting bluetooth Client...")
    did_connect = False
    num_retries = 0
    
    # Try to find UUID service and repear 10 times
    while (not did_connect) and (num_retries < 10):
        print("Client connection attempt number {}...".format(num_retries))
        service_matches = bluetooth.find_service(uuid=uuid, address=None)
        num_retries += 1
        if len(service_matches) != 0:
            did_connect = True
        time.sleep(0.1)

    if not did_connect:
            print("Couldn't find the SampleServer service.")
            sys.exit(0)

    # Get extract parameters from service
    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]        

    print("Connecting to \"{}\" on {}".format(name, host))

    # Create the client socket
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((host, port))

    print("Connected. Sending regular updates")

    # Start persistent loop which sends parameter data to the client
    while not should_quit:
        # Prepare parameter update for client
        parametersJson = prepare_parameters()

        print("Parameters " + parametersJson)

        # Bytes object required for sending to client
        response = bytes(parametersJson, "UTF-8")
     
        # send response via bluetooth
        if not response:
            break

        #Sending data to client via bluetooth
        print(" Sending data via bluetooth")
        sock.send(response)

        time.sleep(10)

    sock.close()


####################################################################
#  
#          Main program
#
####################################################################

if __name__ == "__main__":

    # If bluetooth selected then intiate server and client functions in respective threads
    if use_bluetooth :
        sth = threading.Thread(target=start_server)
        cth = threading.Thread(target=start_client)

        sth.start()
        cth.start()

        cth.join()
        sth.join()

    # If bluetooth not selected then run over wifi
    else :
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()

            try:
                while 1:
                    client, clientInfo = s.accept()
                    print("server recv from: ", clientInfo)
                    data = client.recv(1024)      # receive 1024 Bytes of message in binary format
                    
                    # Action receiced from client (ie forward, left, right, backward or stop)
                    action = data.decode("utf-8") 

                    if action :
                        car_control(action)
                    
                    # Prepare parameter update for client
                    parametersJson = prepare_parameters()

                    # Bytes object required for sending to client
                    response = bytes(parametersJson, "UTF-8")

                    #Sending data to client
                    client.sendall(response)
            except Exception as e: 
                print(e)
                
            finally :
                client.close()
                s.close()

