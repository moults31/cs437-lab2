var server_port=65432;
var server_addr="192.168.68.106";



function move(direction){
    const net=require('net');
    //var input=document.getElementById("myName").value;
    const client=net.createConnection({port: server_port, host: server_addr},() =>{
    //connect listener
    console.log('connected to server!');
    client.write(direction);
     //sock.send(bytes("forward", encoding='utf-8'))
    });
    client.on('data', (data) => {
        //message=JSON.parse(data)
        receive_data(data)
        console.log(data.toString());
        client.end();
        client.destroy();
    });
    
    client.on('end', () => {
        console.log('disconnected from server');
    });
}
function receive_data(data){
    var json_d=JSON.parse(data)
    document.getElementById("CPU_temp").innerHTML = json_d.cpu_temperature+" degrees";
    document.getElementById("PI_temperature").innerHTML = json_d.gpu_temperature +" degrees";
    document.getElementById("battery").innerHTML = json_d.battery+" %";
    document.getElementById("ram").innerHTML = json_d.ram;
    document.getElementById("usage").innerHTML = json_d.cpu_usage+ " %";
    document.getElementById("direction").innerHTML = json_d.direction;
    document.getElementById("speed").innerHTML = json_d.speed+ " m/h";
    
}
     
