import socket
import threading
import random
import os
import queue

messages = queue.Queue()
clients = []
aliases = []


def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        return s.connect_ex(('localhost', port)) == 0



# Configuração do servidor UDP
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
if is_port_in_use(9999):
    client.bind(("localhost", random.randint(8000, 9000)))
else:
    server.bind(("127.0.0.1", 9999)) #Nao preciso dar bind no endereço 
# Configuração do cliente UDP
#client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)




def receive():
    while True:
        try:
            message, addr = server.recvfrom(1024)
            messages.put((message,addr))  # Coloca as mensagens na fila
        except:
            pass

def broadcast():
    while True:
        while not messages.empty():  # Enquanto não esvaziar a fila
            message, addr = messages.get()
            print(message.decode())
            segmentMessage = message.decode('utf-8')
            if "/" in segmentMessage:
                segmentMessage = segmentMessage.split("/")
                print(segmentMessage)
                print(segmentMessage[1])
            else:
                print("No '/' in the message")

            if addr not in clients:  # Caso o endereço não exista, adiciona o usuário no servidor
                clients.append(addr)

                segmentMessage = segmentMessage.split(":")

                aliases.append(segmentMessage[1])

            if segmentMessage[1] == "send":  # Enviar mensagem para um usuário específico
                target = segmentMessage[2]
                if target in aliases:
                    targetIndex = aliases.index(target)
                    server.sendto(message, clients[targetIndex])
            elif segmentMessage[1].startswith("file"):  # Se a mensagem começa com /file
                if segmentMessage[2] == "all":  # Envia o arquivo para todos os clientes conectados
                    filename = segmentMessage[3]
                    print(f"Received file {filename}")
                    message = f"/file/{filename}"
                    for client in clients:
                        try:
                            server.sendto(message.encode(), client)
                        except:
                            clients.remove(client)
                if segmentMessage[2] == "send":  # Envia o arquivo para um usuário específico
                    filename = segmentMessage[4]
                    print(f"Received file {filename}")
                    message = f"/file/{filename}"
                    target = segmentMessage[3]
                    if target in aliases:
                        targetIndex = aliases.index(target)
                        server.sendto(message.encode(), clients[targetIndex])
            else:  # Caso não, envia para todos
                for client in clients:
                    try:
                        if message.decode().startswith("SIGNUP_TAG:"):  # Se começa com SIGNUP_TAG, envia a mensagem de usuário joined
                            name = message.decode()[message.decode().index(":")+1:]
                            server.sendto(f"{name} joined!".encode(), client)
                        else:
                            server.sendto(message,client)
                    except:
                        clients.remove(client)

def send_message():
    name = input("Nickname: ")
    client.sendto(f"SIGNUP_TAG:{name}".encode(), ("127.0.0.1",9999))  # Isso cadastra o usuário no servidor
    while True:
        message = input("")
        if message == "!q":
            exit()
        elif message.startswith("/file"):  # Envia arquivo
            filename = message.split('/')[3]
            if os.path.isfile(filename):
                with open(filename, 'r') as f:
                    lines = f.read()
                message = f"/file/{message.split('/')[2]}/{filename}\\n{lines}"
            client.sendto(f"{name}: {message}".encode(), ("127.0.0.1",9999))
        else:
            client.sendto(f"{name}: {message}".encode(), ("127.0.0.1",9999))

t1 = threading.Thread(target=receive)
t2 = threading.Thread(target=broadcast)
t3 = threading.Thread(target=send_message)

t1.start()
t2.start()
t3.start()
