import sys
import bluetooth
import threading
import socket
import time
import random
import string

if socket.gethostname() != 'raspberrypi':
    address = "E4:5F:01:A3:C7:9C"
    client_port = 1
    server_port = 2
else:
    address = "38:00:25:EB:49:4C"
    client_port = 2
    server_port = 1

def start_server():
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", server_port))
    # server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)

    print("Waiting for connection on RFCOMM channel", server_port)
    client_sock, client_info = server_sock.accept()
    print("Accepted connection from", client_info)

    try:
        while True:
            data = client_sock.recv(1024)
            if not data or data.decode('UTF-8') == "q":
                break
            print("Received", data)
    except OSError:
        pass

    print("Disconnected.")

    client_sock.close()
    server_sock.close()
    print("All done.")

def start_client():
    print("Connecting to \"{}\" on port {}".format(address, client_port))

    # Create the client socket
    sock = None
    did_connect = False
    num_retries = 0

    while (not did_connect) and (num_retries < 10):
        try:
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((address, client_port))
            did_connect = True
        except bluetooth.btcommon.BluetoothError:
            num_retries = num_retries + 1
        time.sleep(1)

    if not did_connect:
        raise Exception("Client exceeded number of allowed connection retries ")

    print("Connected. Type something...")
    while True:
        data = random.choice(string.ascii_letters)
        if not data:
            break
        sock.send(data)

        if data == "q":
            break

        time.sleep(2)
    sock.close()

sth = threading.Thread(target=start_server)
cth = threading.Thread(target=start_client)

sth.start()
cth.start()

cth.join()
sth.join()

print("Success, terminating")



