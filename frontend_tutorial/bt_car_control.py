import sys
import time
import json
import threading
import bluetooth
import pynput
import pprint

from enum import Enum
from threading import Thread

# Bluetooth Universally Unique ID to identify Bluetooth service
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

# Global variables
car_control_char = ''
should_quit = False

# Pynput keyboard listener callbacks
def on_press(key):
    global car_control_char
    if 'char' in dir(key):
        car_control_char = key.char

def on_release(key):
    pass

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
                                # protocols=[bluetooth.OBEX_UUID]
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
                print("Received q. Server exiting.")
                break

            # Decode and print car info
            car_info = json.loads(data.decode('UTF-8'))
            print('\n')
            pprint.pprint(car_info)

    except OSError:
        pass

    print("Server disconnected.")

    client_sock.close()
    server_sock.close()
    print("Server socket closed.")

# Start bluetooth client for sending data to front end
def start_client():
    # Import var containing car control character
    global car_control_char
    global should_quit

    print("Starting bluetooth Client...")
    did_connect = False
    num_retries = 0
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

    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]        

    print("Client connecting to \"{}\" on {}".format(name, host))

    # Create the client socket
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((host, port))

    print("Client connected.")

    # Listen for keypresses
    listener = pynput.keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    car_control_char_prev = ''

    print("Control the car with WASD. q to quit.")
    while not should_quit:
        if car_control_char == "q":
            "Received q, sending quit signal."
            should_quit = True
            break

        if car_control_char != car_control_char_prev:
            # Car control character changed, send it to the car
            print("Sending {}".format(car_control_char))
            sock.send(car_control_char)
            car_control_char_prev = car_control_char

    sock.close()


if __name__ == "__main__":
    # Initiate server and client functions in respective threads
    sth = threading.Thread(target=start_server)
    cth = threading.Thread(target=start_client)

    sth.start()
    cth.start()

    sth.join()
    cth.join()