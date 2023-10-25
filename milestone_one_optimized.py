import sys
import socket
from time import sleep, perf_counter
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
SLEEP_SQUISH_SECONDS = 0.01


current_timeout_seconds = INITIAL_TIMEOUT_SECONDS
size_message = "SendSize\nReset\n\n"

successful_requests = 0
failed_requests = 0

MAX_SIZE = -1
MAX_ATTEMPTS = 100
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(INITIAL_TIMEOUT_SECONDS)
sock.sendto(size_message.encode("utf-8"), (UDP_IP, UDP_PORT))
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

remaining_offsets = OrderedDict()
file = []
for i in range(0, MAX_SIZE, MAX_BYTES):
    remaining_offsets[i] = 0
    file.append("")

squished_requests = 0

try:
    while len(remaining_offsets) > 0:
        accepted_offsets = []
        print(f"Remaining offsets: {len(remaining_offsets)}")
        for offset in remaining_offsets:
            num_bytes = min(MAX_BYTES, MAX_SIZE - offset)
            request_message = f"Offset: {offset}\nNumBytes: {num_bytes}\n\n"
            try:
                sock.sendto(request_message.encode("utf-8"), (UDP_IP, UDP_PORT))
            except:
                print("Error sending request to server")
                exit(1)
            try:
                response_bytes, addr = sock.recvfrom(SOCKET_RECEIVE_BYTES)
                response_data = response_bytes.decode("utf-8")
                if not response_data.startswith("Offset: "):
                    continue
                response_tokens = response_data.split("\n")
                response_offset = int(response_tokens[0].split(":")[1])
                response_numbytes = int(response_tokens[1].split(":")[1])
                content = ""
                if (response_tokens[2] == "Squished"):
                    content = "\n".join(response_tokens[4:])
                    squished_requests += 1
                    sleep(SLEEP_SQUISH_SECONDS)
                else:
                    content = "\n".join(response_tokens[3:])
                current_timeout_seconds *= TIMEOUT_DECREASE_FACTOR
                sock.settimeout(current_timeout_seconds)
                sleep(SLEEP_SECONDS)
                if ((response_offset in remaining_offsets) and (len(file[response_offset // MAX_BYTES]) == 0)):
                    accepted_offsets.append(response_offset)
                    file[response_offset // MAX_BYTES] = content
                    # print(f"received response in {round(response_time, 5)} seconds")
                    successful_requests += 1

            except socket.timeout:
                failed_requests += 1
                current_timeout_seconds *= TIMEOUT_INCREASE_FACTOR
                sock.settimeout(current_timeout_seconds)
        for offset in accepted_offsets:
            remaining_offsets.pop(offset)
except KeyboardInterrupt:
    print(f"Remaining offsets: {len(remaining_offsets)}")
    print(f"Socket timeout: {current_timeout_seconds}")
    exit(1)


file_data = "".join(file)
print(f"Bytes of data received: {len(file_data)}")

file_data_hash = hashlib.md5(file_data.encode("utf-8")).hexdigest()
print(f"MD5 hash: {file_data_hash}")

submit_message = f"Submit: 2021CS10099_2021CS10581@slowbrains\nMD5: {file_data_hash}\n\n"
sock.sendto(submit_message.encode("utf-8"), (UDP_IP, UDP_PORT))


while True:
    try:
        data, addr = sock.recvfrom(SOCKET_RECEIVE_BYTES);
        submit_response = data.decode("utf-8")
        if submit_response.__contains__("Result: ") and submit_response.__contains__("Time: ") and submit_response.__contains__("Penalty: "):
            print("---------------------------------")
            print(submit_response[:-2])
            print("---------------------------------")
            break
    except:
        pass


print(f"Successful requests: {successful_requests}")
print(f"Failed requests: {failed_requests}")
print(f"Squished requests: {squished_requests}")
print(f"Final timeout: {current_timeout_seconds}")
