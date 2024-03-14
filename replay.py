import os
import socket
import atexit
import time

def record_packets(remote_socket, client_socket, recorded_packets):
    while True:
        data = remote_socket.recv(4096)
        if not data:
            break
        recorded_packets.append(data)
        client_socket.sendall(data)  # Forwarding data to client while recording
    return recorded_packets

def playback_packets(client_socket, recorded_packets, delay):
    for packet in recorded_packets:
        client_socket.sendall(packet)
        time.sleep(delay)

def save_recorded_packets(file_path, recorded_packets):
    try:
        with open(file_path, 'wb') as f:
            for packet in recorded_packets:
                f.write(packet)
        print("File saved successfully.")
        print("Recorded packets:", recorded_packets)  # Debug print
    except Exception as e:
        print("Error writing to file:", e)

def proxy_server(remote_host, remote_port, mode, delay=1):
    local_host = '127.0.0.1'
    local_port = 8888
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'recorded_packets.packets')
    print("File path:", file_path)

    recorded_packets = []
    atexit.register(save_recorded_packets, file_path, recorded_packets)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy_socket:
        proxy_socket.bind((local_host, local_port))
        proxy_socket.listen(1)
        print("Proxy server started on {}:{}".format(local_host, local_port))

        while True:
            client_socket, addr = proxy_socket.accept()
            print("Connection accepted from:", addr)

            if mode == 'record':
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_socket:
                    remote_socket.connect((remote_host, remote_port))
                    while True:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                        remote_socket.sendall(data)
                        remote_response = remote_socket.recv(4096)
                        if not remote_response:
                            break
                        client_socket.sendall(remote_response)
                        recorded_packets.append(remote_response)
                
            elif mode == 'playback':
                with open(file_path, 'rb') as f:
                    recorded_packets = [packet for packet in f.read().split(b'\r\n')]
                    playback_packets(client_socket, recorded_packets, delay)
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_socket:
                    remote_socket.connect((remote_host, remote_port))
                    while True:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                        remote_socket.sendall(data)
                        remote_response = remote_socket.recv(4096)
                        if not remote_response:
                            break
                        client_socket.sendall(remote_response)

            client_socket.close()

if __name__ == '__main__':
    remote_host = input("Enter remote host: ")
    remote_port = int(input("Enter remote port: "))
    mode = input("Enter mode (record/playback): ")
    delay = float(input("Enter delay between packets during playback (in seconds): "))

    proxy_server(remote_host, remote_port, mode, delay)
