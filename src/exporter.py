import subprocess
import json
import datetime
import time
import os
from prometheus_client import start_http_server, Gauge

def bytes_to_bits(bytes_per_sec):
    return bytes_per_sec * 8

def bits_to_megabits(bits_per_sec):
    megabits = round(bits_per_sec * (10**-6),2)
    return str(megabits) + " Mb/s"

def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

def run_speedtest():
    print('Starting speedtest')
    cmd = ["speedtest", "--format=json-pretty", "--progress=no", "--accept-license", "--accept-gdpr"]
    server = os.environ.get('SPEEDTEST_SERVER')
    if server:
        if server.isnumeric():
            print("Using custom server ID: "+str(server))
            cmd.append("--server-id=" + str(server))

    while True:
        try:
            output = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            output = e.output
        if is_json(output):
            data = json.loads(output)
            if "error" in data:
                # If we get here it probably means that socket timed out(Network issues?)
                print('Something went wrong')
                print(data['error'])
                return None
            if "type" in data:
                if data['type'] == 'log':
                    print(str(data["timestamp"]) + " - " + str(data["message"]))
                if data['type'] == 'result':
                    actual_server = int(data['server']['id'])
                    actual_ping = int(data['ping']['latency'])
                    download = bytes_to_bits(data['download']['bandwidth'])
                    upload = bytes_to_bits(data['upload']['bandwidth'])
                    return (actual_server, actual_ping, download, upload)

def update_results(test_done):
    server.set(test_done[0]) 
    ping.set(test_done[1])
    download_speed.set(test_done[2])
    upload_speed.set(test_done[3])
    current_dt = datetime.datetime.now()
    print(current_dt.strftime("%d/%m/%Y %H:%M:%S - ") + "Server: " + str(test_done[0]) + "| Ping: " + str(test_done[1]) + " ms | Download: " + bits_to_megabits(test_done[2]) + " | Upload:" + bits_to_megabits(test_done[3]))

def run(http_port, sleep_time):
    start_http_server(http_port)
    print("Successfully started Speedtest Exporter on http://localhost:" + str(http_port))
    while True:
        test = run_speedtest()
        if isinstance(test, tuple):
            update_results(test)
            time.sleep(sleep_time)

if __name__ == '__main__':
    # Create the Metrics
    server = Gauge('speedtest_server_id', 'Speedtest server ID used to test')
    ping = Gauge('speedtest_ping_latency_milliseconds', 'Speedtest current Ping in ms')
    download_speed = Gauge('speedtest_download_bits_per_second', 'Speedtest current Download Speed in bit/s')
    upload_speed = Gauge('speedtest_upload_bits_per_second', 'Speedtest current Upload speed in bits/s')
    server_port = os.environ.get('SPEEDTEST_PORT')
    if server_port:
        PORT=int(server_port)
    else:
        PORT=9800
    SLEEP=95
    run(PORT, SLEEP)
