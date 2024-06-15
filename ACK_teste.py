import socket
import threading
import os
import time

# Defina client_socket como uma variável global
client_socket = None

# Adicione um timeout ao socket para esperar pela resposta ACK
ACK_TIMEOUT = 2  # segundos

def start_client(port, peer_ip, peer_port):
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('localhost', port))
    client_socket.settimeout(ACK_TIMEOUT)

def send(peer_ip, peer_port):
    while True:
        msg = input("Digite a mensagem para enviar: ")        
        if os.path.isfile(msg):
            with open(msg, 'r') as f:
                lines = f.read()
            msg = f"{msg}\\n{lines}"
        
        client_socket.sendto(msg.encode(), (peer_ip, peer_port))
        
        # Aguarde pela resposta ACK
        try:
            ack, _ = client_socket.recvfrom(1024)
            print(f"ACK recebido para a mensagem: {msg.split('\\n')[0]}")
        except socket.timeout:
            print("Timeout: ACK não recebido.")

def receive():
    while True:
        try:
            data, addr = client_socket.recvfrom(1024)
            filename = data.decode().split('\\n')[0]
            content = '\\n'.join(data.decode().split('\\n')[1:])
            content = content + "PPP" + "\n"
            
            with open(filename, 'w') as f:
                f.write(content)
            
            print(f"Arquivo recebido: {filename}")
            
            # Envie uma resposta ACK
            ack_msg = "ACK"
            client_socket.sendto(ack_msg.encode(), addr)
            
        except Exception as e:
            print(f"Erro: {e}")
            
            
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
