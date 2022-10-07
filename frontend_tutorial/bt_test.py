import socket
import sys
from enum import Enum
import time
import json
import threading
from threading import Thread
import bluetooth
import random
import string

# Bluetooth Universally Unique ID to identify Bluetooth service
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

# Initiate bluetooth server
def start_server():
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
        while True:
            data = client_sock.recv(1024)
            if not data:
                print("Received empty buffer. Server exiting.")
                break
            if data.decode('UTF-8') == "q":
                print("Received q. Server exiting.")
                break
            print("Received", data)
            
    except OSError:
        pass

    print("Server disconnected.")

    client_sock.close()
    server_sock.close()
    print("Server socket closed.")

def alternative_client():
    target_name = "raspberrypi"
    target_address = None

    nearby_devices = bluetooth.discover_devices()

    for bdaddr in nearby_devices:
        print(bluetooth.lookup_name( bdaddr ))
        if target_name == bluetooth.lookup_name( bdaddr ):
            target_address = bdaddr
            break

    if target_address is not None:
        print ("found target bluetooth device with address ", target_address)
    else:
        print ("could not find target bluetooth device nearby")
        return

    x = {
    "name": "John",
    "age": 30,
    "city": "New York"
    }

    # convert into JSON:
    y = json.dumps(x)

    port = 1

    sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
    sock.connect((target_address, port))

    sock.send(y)

    sock.close()                

# Start bluetooth client for sending data to front end
def start_client():

    print("Starting bluetooth Client...")

    did_connect = False
    num_retries = 0
    while (not did_connect) and (num_retries < 10):
        print("Client connection attempt number {}...".format(num_retries))
        service_matches = bluetooth.find_service(uuid=uuid, address=None)
        num_retries += 1
        if len(service_matches) != 0:
            did_connect = True
        time.sleep(1)

    if not did_connect:
            print("Couldn't find the SampleServer service.")
            sys.exit(0)

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
    while True:
        data = random.choice(string.ascii_letters)
        if not data:
            break
        sock.send(data)

        if data == "q":
            break

        time.sleep(2)

    sock.close()


if __name__ == "__main__":
    # Initiate server and client functions in respective threads
    sth = threading.Thread(target=start_server)
    cth = threading.Thread(target=start_client)
    # cth = threading.Thread(target=alternative_client)

    sth.start()
    cth.start()

    sth.join()
    cth.join()