import socket
import threading
import os

# Defina client_socket como uma variável global
client_socket = None

def start_client(port, peer_ip, peer_port):
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('localhost', port))

def send(peer_ip, peer_port):
    while True:
        msg = input("")        
        #print(filename)
        if os.path.isfile(msg):
            with open(msg, 'r') as f:
                lines = f.read()
            msg = f"{msg}\\n{lines}"
        
        client_socket.sendto(msg.encode(), (peer_ip, peer_port))
    
def receive():
    while True:
        try:
            data, addr = client_socket.recvfrom(1024)
            filename =  data.decode().split('\\n')[0]
            content = '\\n'.join(data.decode().split('\\n')[1:])
            content = content + "PPP"+ "\n" #Teste se atualiza o documento
            with open(filename, 'w') as f:
                f.write(content)
            print(f"Received file {filename}")
            
            #print("Mensagem recebida: ", data.decode(), " de: ", addr)
        except:
            pass    
        
#---------------------------------------
#Aqui escolho qual dos dois clients quero ser

escolha = int(input("Escolha qual client se deseja: 1 - Client Sender | 2 - Client Receiver \n"))

if escolha == 1:
    start_client(12345, 'localhost', 12346)
    t1 = threading.Thread(target=send, args=('localhost', 12346))
elif escolha == 2:
    start_client(12346, 'localhost', 12345)
    t1 = threading.Thread(target=send, args=('localhost', 12345))
else:
    print("escolha invalida")

t2 = threading.Thread(target=receive)
t1.start()
t2.start()
