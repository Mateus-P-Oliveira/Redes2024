import socket
import threading
import os
import time

# Defina client_socket como uma variável global
client_socket = None
ack_counter = 0
# Adicione um timeout ao socket para esperar pela resposta ACK
ACK_TIMEOUT = 2  # segundos

def start_client(port, peer_ip, peer_port):
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('localhost', port))
   # client_socket.settimeout(ACK_TIMEOUT)
   
def dividir_arquivo(nome_arquivo):
    # Lê o arquivo e armazena o conteúdo em uma variável
    
    with open(nome_arquivo, 'r') as arquivo:
        conteudo = arquivo.read()
        
    conteudo = f"{nome_arquivo}\\n{conteudo}"
    
    # Codifica o conteúdo do arquivo em bytes
    conteudo_bytes = conteudo.encode('utf-8')
    
    # Divide o conteúdo do arquivo em partes de 10 bytes
    partes = [conteudo_bytes[i:i+10] for i in range(0, len(conteudo_bytes), 10)]
    
    # Adiciona padding ao último pacote se ele não tiver 10 bytes
    if len(partes[-1]) < 10:
        partes[-1] += b' ' * (10 - len(partes[-1]))  # Preenche com espaços em branco
    
    return partes
    

# Variáveis globais para controle do slow start
cwnd = 1  # Tamanho inicial da janela de congestionamento (Congestion Window)
ssthresh = 64  # Limiar inicial para o slow start

def send(peer_ip, peer_port):
    global ack_counter, cwnd, ssthresh
    partes_msg = []  # Lista para armazenar as partes da mensagem

    while True:
        msg = input("Digite o nome do arquivo para enviar: ")
        
        if msg:  # Verifica se um nome de arquivo foi digitado
            if os.path.isfile(msg):
                partes_msg = dividir_arquivo(msg)
                break  # Sai do loop após dividir o arquivo

    # Índice para controlar qual parte da mensagem está sendo enviada
    send_index = 0

    while send_index < len(partes_msg):
        try:
            # Envia pacotes conforme o tamanho da janela de congestionamento
            for i in range(send_index, min(send_index + cwnd, len(partes_msg))):
                client_socket.sendto(partes_msg[i], (peer_ip, peer_port))
                print(f"Enviando parte {i+1} de {len(partes_msg)}")
            
            # Defina um timeout antes de esperar pelo ACK
            client_socket.settimeout(ACK_TIMEOUT)

            # Espera por ACKs para todas as partes enviadas na janela
            for _ in range(cwnd):
                ack, _ = client_socket.recvfrom(1024)
                ack_counter += 1  # Incrementa o contador de ACKs
                print(f"ACK recebido. Contador de ACKs: {ack_counter}")
                send_index += 1  # Move para a próxima parte da mensagem

            # Dobra o tamanho da janela de congestionamento após receber todos os ACKs
            if cwnd < ssthresh:
                cwnd *= 2
            else:
                cwnd += 1  # Crescimento linear após atingir o limiar

        except socket.timeout:
            print("Timeout: ACK não recebido.")
            ssthresh = cwnd // 2  # Reduz o limiar pela metade
            cwnd = 1  # Reinicia o tamanho da janela de congestionamento
            ack_counter = 0  # Reinicia o contador de ACKs
            print(f"Contador de ACKs reiniciado para: {ack_counter}")
        
        # Remova o timeout após tentar receber os ACKs
        client_socket.settimeout(None)


def receive():
    buffer = ""  # Inicializa um buffer como uma string vazia
    while True:
        try:
            data, addr = client_socket.recvfrom(1024)
            # Decodifica os dados de bytes para string e anexa ao buffer
            buffer += data.decode()           
           
            # Verifica se o delimitador '\\n' está presente no buffer
            if '\\n' in buffer:
                filename, filecontent = buffer.split('\\n', 1)
                # Remova o padding (espaços em branco) do final do conteúdo do arquivo
                filecontent = filecontent.rstrip(' ')
                print("---!!!!---")
                print(filename)
                print("--------")
                print(filecontent)
                # Escreva o conteúdo remontado no arquivo
                with open(filename, 'w') as f:
                    f.write(filecontent)
                
                print(f"Arquivo {filename} recebido e remontado.")
                break  # Sai do loop após reconstruir o arquivo
            else:
                print("Dados recebidos não contêm o delimitador '\\n' esperado.")
            # Envie uma resposta ACK
            ack_msg = "ACK"
            client_socket.sendto(ack_msg.encode(), addr)
            
        except Exception as e:
            print(f"Erro: {e}")
            break  # Sai do loop em caso de erro

            
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
