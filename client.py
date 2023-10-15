import sys
import socket
from time import sleep
import hashlib
from collections import OrderedDict

if len(sys.argv) < 3:
    print("Server IP Address and port required as arguments")
    exit(1)

UDP_IP = sys.argv[1]
UDP_PORT = int(sys.argv[2])
MAX_BYTES = 1448
SOCKET_RECEIVE_BYTES = 2048
SLEEP_SECONDS = 0.003
INITIAL_TIMEOUT_SECONDS = 0.01
TIMEOUT_DECREASE_FACTOR = 0.95
TIMEOUT_INCREASE_FACTOR = 1.2


curr_timeout = INITIAL_TIMEOUT_SECONDS
size_message = b"SendSize\nReset\n\n"

successful_requests = 0
failed_requests = 0

MAX_SIZE = -1
MAX_ATTEMPTS = 100
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(curr_timeout)
sock.sendto(size_message, (UDP_IP, UDP_PORT))
for _ in range(MAX_ATTEMPTS):
    try:
        size_data, addr = sock.recvfrom(SOCKET_RECEIVE_BYTES);
        MAX_SIZE = int(size_data.decode("utf-8").split(":")[1])
        break;
    except:
        pass

if (MAX_SIZE == -1):
    print("Unable to receive data from the server")
    exit(1)
print(f"Max Size: {MAX_SIZE}")

remaining_offsets = OrderedDict.fromkeys(list(range(0, MAX_SIZE, MAX_BYTES)))
file = []
for i in range(0, MAX_SIZE, MAX_BYTES):
    file.append("")

while len(remaining_offsets) > 0:
    accepted_offsets = []
    print(f"Remaining offsets: {len(remaining_offsets)}")
    for offset in remaining_offsets:
        num_bytes = min(MAX_BYTES, MAX_SIZE - offset)
        request_message = f"Offset: {offset}\nNumBytes: {num_bytes}\n\n"
        header_bytes = len(request_message)
        sock.sendto(request_message.encode("utf-8"), (UDP_IP, UDP_PORT))
        try:
            response_data, addr = sock.recvfrom(SOCKET_RECEIVE_BYTES)
            response_list = response_data.decode("utf-8").split("\n")
            if not response_list[0].startswith("Offset: "):
                continue
            response_offset = int(response_list[0].split(":")[1])
            response_bytes = int(response_list[1].split(":")[1])
            content = "\n".join(response_list[3:])
            if ((response_offset in remaining_offsets) and (len(file[response_offset // MAX_BYTES]) == 0) and (response_bytes == len(content))):
                accepted_offsets.append(response_offset)
                file[response_offset // MAX_BYTES] = content
                # print(f"received response in {round(response_time, 5)} seconds")
                successful_requests += 1
                curr_timeout *= TIMEOUT_DECREASE_FACTOR
                sock.settimeout(curr_timeout)
            sleep(SLEEP_SECONDS)

        except socket.timeout:
            failed_requests += 1
            curr_timeout *= TIMEOUT_INCREASE_FACTOR
            sock.settimeout(curr_timeout)

    for offset in accepted_offsets:
        remaining_offsets.pop(offset)


file_data = ""
for content in file:
    file_data += content
print(f"Bytes of data received {len(file_data)}")

file_data_hash = hashlib.md5(file_data.encode("utf-8")).hexdigest()
print(f"MD5 hash: {file_data_hash}")

submit_message = bytes(f"Submit: 2021CS10099_2021CS10581@slowbrains\nMD5: {file_data_hash}\n\n", encoding="utf-8")
sock.sendto(submit_message, (UDP_IP, UDP_PORT))


while True:
    try:
        data, addr = sock.recvfrom(SOCKET_RECEIVE_BYTES);
        submit_response = data.decode("utf-8")
        if submit_response.__contains__("Result: ") and submit_response.__contains__("Time: ") and submit_response.__contains__("Penalty: "):
            print(submit_response)
            break
    except:
        pass


print(f"Successful requests: {successful_requests}")
print(f"Failed requests: {failed_requests}")
print(f"Final timeout: {curr_timeout}")
