import socket
import threading
import os
import time

# Defina client_socket como uma variável global
client_socket = None
ack_counter = 0
# Adicione um timeout ao socket para esperar pela resposta ACK
ACK_TIMEOUT = 2  # segundos


def calculate_crc(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
    return crc & 0xFFFF


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
        while True:
            msg = input("Digite o nome do arquivo para enviar: ")
            
            if msg:  # Verifica se um nome de arquivo foi digitado
                if os.path.isfile(msg):
                    partes_msg = dividir_arquivo(msg)
                    break  # Sai do loop após dividir o arquivo

        # Índice para controlar qual parte da mensagem está sendo enviada
        send_index = 0
        sequence_number = 0  # Número de sequência inicial
        
        while send_index < len(partes_msg):
            try:
                # Prepara o pacote com número de sequência e CRC
                
            
                # Envia pacotes conforme o tamanho da janela de congestionamento
                for i in range(send_index, min(send_index + cwnd, len(partes_msg))):
                    seq_and_crc = sequence_number.to_bytes(2, 'big') + partes_msg[i]
                    crc = calculate_crc(seq_and_crc)
                    packet = seq_and_crc + crc.to_bytes(2, 'big')
                    print("------")
                    print(seq_and_crc)
                    print("///////////")
                    print(packet)
                    client_socket.sendto(packet, (peer_ip, peer_port))
                    print(f"Enviando parte {i+1} de {len(partes_msg)} com número de sequência {sequence_number}")
                    sequence_number = (sequence_number + 1) % 256  # Incrementa o número de sequência

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
                send_index = max(send_index - cwnd, 0)  # Decrementa send_index ou vai para 0
                print(f"Contador de ACKs reiniciado para: {ack_counter}")

            # Remova o timeout após tentar receber os ACKs
            client_socket.settimeout(None)



def receive():
    buffer = {}  # Dicionário para armazenar partes recebidas
    expected_seq = 0  # Número de sequência esperado inicial
    
    while True:
        try:
            data, addr = client_socket.recvfrom(1024)
            sequence_number = int.from_bytes(data[:2], 'big')
            content = data[2:-2]  # Assume that the last two bytes are CRC


            # Calcula o CRC recebido e compara com o calculado
            received_crc = int.from_bytes(data[-2:], 'big')
            calculated_crc = calculate_crc(data[:-2])
            print("UUUUUUUUUU")
            print(received_crc)
            print("********")
            print(calculated_crc)
           
            if received_crc == calculated_crc:
                if sequence_number == expected_seq:
                    buffer[sequence_number] = content
                    expected_seq = (expected_seq + 1) % 256
                    ack_msg = expected_seq.to_bytes(2, 'big') + b"ACK"
                    client_socket.sendto(ack_msg, addr)
                else:
                    # Send ACK for the last in-order packet received
                    last_ack_seq = (expected_seq - 1) % 256
                    ack_msg = last_ack_seq.to_bytes(2, 'big') + b"ACK"
                    client_socket.sendto(ack_msg, addr)
            else:
                print("Erro de CRC. Pacote descartado.")

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
