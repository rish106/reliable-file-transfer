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


curr_timeout = 0.01


first_message = b"SendSize\nReset\n\n"

print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % first_message.decode("utf-8"))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(first_message, (UDP_IP, UDP_PORT))
size_data, addr = sock.recvfrom(1024);
# print(f"received message: {size_data.decode('utf-8')}")
max_size = int(size_data.decode("utf-8").split(":")[1])
print(f"Max Size: {max_size}")

offset = 0
successful_requests = 0
failed_requests = 0
sock.settimeout(curr_timeout)
file_data = ""
remaining_offsets = OrderedDict.fromkeys(list(range(0, max_size, MAX_BYTES)))
file = []
for i in range(0, max_size, MAX_BYTES):
    file.append("")

while len(remaining_offsets) > 0:
    accepted_offsets = {}
    print(f"Remaining offsets: {len(remaining_offsets)}")
    for offset in remaining_offsets:
        num_bytes = min(MAX_BYTES, max_size - offset)
        request_message = f"Offset: {offset}\nNumBytes: {num_bytes}\n\n"
        header_bytes = len(request_message)
        sock.sendto(request_message.encode("utf-8"), (UDP_IP, UDP_PORT))
        try:
            response_data, addr = sock.recvfrom(2048)
            response_list = response_data.decode("utf-8").split("\n")
            if response_list[0].find("Offset: ") == -1:
                continue
            response_offset = int(response_list[0].split(":")[1])
            response_bytes = int(response_list[1].split(":")[1])
            line = "\n".join(response_list[3:])
            if ((response_offset in remaining_offsets) and (response_offset not in accepted_offsets) and (response_bytes == len(line))):
                accepted_offsets[offset] = 0
                file[response_offset // MAX_BYTES] = line[0:response_bytes]
                # print(f"received response in {round(response_time, 5)} seconds")
                successful_requests += 1
                curr_timeout *= 0.95
                sock.settimeout(curr_timeout)
            sleep(0.003)
                
        except socket.timeout:
            failed_requests += 1
            curr_timeout *= 1.2
            sock.settimeout(curr_timeout)

    for offset in accepted_offsets:
        remaining_offsets.pop(offset)


for content in file:
    file_data += content
print(f"Bytes of data received {len(file_data)}")
# print(file_data)
print()
file_data_hash = hashlib.md5(file_data.encode("utf-8")).hexdigest()
print(f"MD5 hash: {file_data_hash}")
submit_message = bytes(f"Submit: 2021CS10581@slowbrains\nMD5: {file_data_hash}\n\n", encoding="utf-8")
sock.sendto(submit_message, (UDP_IP, UDP_PORT))


while True:
    try:
        data, addr = sock.recvfrom(1024);
        submit_response = data.decode("utf-8")
        if submit_response.__contains__("Result: ") and submit_response.__contains__("Time: ") and submit_response.__contains__("Penalty: "):
            print(f"{submit_response}")
            break
    except socket.timeout:
        pass


print(f"Successful requests: {successful_requests}")
print(f"Failed requests: {failed_requests}")
print(f"Final timeout: {curr_timeout}")
