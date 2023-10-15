import socket
from time import perf_counter
import hashlib

UDP_IP = "127.0.0.1"
UDP_PORT = 9801
MAX_BYTES = 1448
SOCKET_TIMEOUT = 0.01875


first_message = b"SendSize\nReset\n\n"
send_times = {}

print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % first_message.decode('utf-8'))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(first_message, (UDP_IP, UDP_PORT))
size_data, addr = sock.recvfrom(1024);
# print(f"received message: {size_data.decode('utf-8')}")
max_size = int(size_data.decode("utf-8").split(":")[1])
print(f"Max Size: {max_size}")

offset = 0
successful_requests = 0
failed_requests = 0
sock.settimeout(SOCKET_TIMEOUT)
file_data = ""

while offset < max_size:
    num_bytes = min(MAX_BYTES, max_size - offset)
    request_message = f"Offset: {offset}\nNumBytes: {num_bytes}\n\n"
    header_bytes = len(request_message)
    if offset not in send_times:
        send_times[offset] = perf_counter()
    sock.sendto(request_message.encode("utf-8"), (UDP_IP, UDP_PORT))
    try:
        response_data, addr = sock.recvfrom(num_bytes + header_bytes)
        response_time = perf_counter() - send_times[offset]
        response_list = response_data.decode("utf-8").split("\n")
        response_offset = int(response_list[0].split(":")[1])
        line = "\n".join(response_list[3:])
        if (response_offset == offset):
            file_data += line
            # print(f"received response in {round(response_time, 5)} seconds")
            offset += num_bytes
            successful_requests += 1
    except socket.timeout:
        # print("socket timed out")
        failed_requests += 1
print(f"Bytes of data received {len(file_data)}")
# print(file_data)
print()
file_data_hash = hashlib.md5(file_data.encode("utf-8")).hexdigest()
print(f"MD5 hash: {file_data_hash}")
submit_message = bytes(f"Submit: 2021CS10581@slowbrains\nMD5: {file_data_hash}\n\n", encoding="utf-8")
sock.sendto(submit_message, (UDP_IP, UDP_PORT))
submit_response, addr = sock.recvfrom(1024);
print(f"{submit_response.decode('utf-8')}")
print(f"Successful requests: {successful_requests}")
print(f"Failed requests: {failed_requests}")
