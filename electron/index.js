document.onkeydown = updateKey;
document.onkeyup = resetKey;

var server_port = 65432;
var server_addr = "192.168.1.133";   // the IP address of your Raspberry PI

function client(){
    
    const net = require('net');
    var input = document.getElementById("message").value;

    const client = net.createConnection({ port: server_port, host: server_addr }, () => {
        // 'connect' listener.
        console.log('connected to server!');
        // send the message
        client.write(`${input}\r\n`);
    });
    
    // get the data from the server
    client.on('data', (data) => {
        document.getElementById("bluetooth").innerHTML = data;
        console.log(data.toString());
        client.end();
        client.destroy();
    });

    if (!('bluetooth' in navigator)) {
        console.log('Bluetooth API not supported on your browser.');
    } else {
        console.log('CONGRATS! Bluetooth API supported on your browser.');
    }

    client.on('end', () => {
        console.log('disconnected from server');
    });


}

// for detecting which key is been pressed w,a,s,d
function updateKey(e) {

    e = e || window.event;

    if (e.keyCode == '87') {
        // up (w)
        document.getElementById("upArrow").style.color = "green";
        // send_data("87");
    }
    else if (e.keyCode == '83') {
        // down (s)
        document.getElementById("downArrow").style.color = "green";
        // send_data("83");
    }
    else if (e.keyCode == '65') {
        // left (a)
        document.getElementById("leftArrow").style.color = "green";
        // send_data("65");
    }
    else if (e.keyCode == '68') {
        // right (d)
        document.getElementById("rightArrow").style.color = "green";
        // send_data("68");
    }
}

// reset the key to the start state 
function resetKey(e) {

    e = e || window.event;

    document.getElementById("upArrow").style.color = "grey";
    document.getElementById("downArrow").style.color = "grey";
    document.getElementById("leftArrow").style.color = "grey";
    document.getElementById("rightArrow").style.color = "grey";
}


// update data for every 50ms
function update_data(){
    setInterval(function(){
        // get image from python server
        client();
    }, 50);
}

function bt_connect(){
    var BluetoothHciSocket = require('bluetooth-hci-socket');
    var bluetoothHciSocket = new BluetoothHciSocket();
    var filter = new Buffer(14);
    bluetoothHciSocket.setFilter(filter);
    // var btSerial = new (require("node-bluetooth").BluetoothSerialPort)();
    // var btSerial = new (require("bluetooth-serial-port").BluetoothSerialPort)();

    // var name = 'raspberrypi'

    // btSerial.on("found", function (address, name) {
    //     console.log("address1: ", address);
    //     console.log("name1: ", name);
    //     btSerial.findSerialPortChannel(
    //         address,
    //         function (channel) {
    //             btSerial.connect(
    //                 address,
    //                 channel,
    //                 function () {
    //                     console.log("connected");

    //                     btSerial.write(
    //                         Buffer.from("my data", "utf-8"),
    //                         function (err, bytesWritten) {
    //                             if (err) console.log(err);
    //                         }
    //                     );

    //                     btSerial.on("data", function (buffer) {
    //                         console.log(buffer.toString("utf-8"));
    //                     });
    //                 },
    //                 function () {
    //                     console.log("cannot connect");
    //                 }
    //             );

    //             // close the connection when you're ready
    //             btSerial.close();
    //         },
    //         function () {
    //             console.log("found nothing");
    //         }
    //     );
    // });

    // btSerial.inquire();
}