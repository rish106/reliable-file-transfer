#!/usr/bin/env bash

if [[ $# -ne 1 ]]; then
    echo "Line count required as argument"
    exit 1
fi

line_cnt="$1"

if [[ $(($(ps -ef | grep "java UDPServer" | wc -l))) -gt 1 ]]; then
    kill -9 $(ps -ef | grep "java UDPServer" | grep "/usr/bin/java" | head -n 1 | awk '{print $2}')
fi

false_cnt=0
true_cnt=0

for ((i = 0; i < 10; i++)); do
    java UDPServer 9801 big.txt.1 "$line_cnt" constantrate notournament verbose > /dev/null &
    sleep 0.5 &&
    output="$(python3 client.py)"
    if [[ ! $(echo "$output" | grep "Result: true") ]]; then
        echo "Result false :("
        false_cnt=$((false_cnt + 1))
    else
        true_cnt=$((true_cnt + 1))
    fi
    kill -9 $(ps -ef | grep "java UDPServer" | grep "/usr/bin/java" | head -n 1 | awk '{print $2}') > /dev/null
    sleep 0.5
done

echo "Successful submits: $true_cnt"
echo "Failed submits: $false_cnt"
