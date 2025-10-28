import subprocess
import json
import csv
from httplib2 import Http
from datetime import datetime

# --- UPDATED FUNCTION ---
# Handles multiple IPs in one row (comma-separated)
def load_ip_addresses(csv_file='ip_addresses.csv'):
    ip_addresses = {}
    with open(csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['Name'].strip()
            # Split all comma-separated IPs and clean spaces
            ip_list = [ip.strip() for ip in row['IP'].split(',') if ip.strip()]
            ip_addresses[name] = ip_list
    return ip_addresses


testcenter_server = 'http://pdx-lic.schrodinger.com:47001'
#chat_room_webhook = 'https://chat.googleapis.com/v1/spaces/AAAALvuQgJk/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=-STnqiO4YVMdh3SoymKOEng1L1KiV6gHxaRcoHy3JcY%3D'
chat_room_webhook = 'https://chat.googleapis.com/v1/spaces/AAAA2_Jm56c/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=CPYdBbQu97OMdqsF7hZVo8EYXjC2LbDFXChbfEqc-r8%3D'


def get_current_usage(license_type):
    lic_stats = subprocess.run(
        ["curl", "-s", f"{testcenter_server}/v1/statistics"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    data = json.loads(lic_stats.stdout)
    if data:
        return data['activeLicenses'][license_type]['current']


def get_ip_info(license_type):
    clients_info = subprocess.run(
        ["curl", "-s", f"{testcenter_server}/v1/clients"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    data = json.loads(clients_info.stdout)

    ips_consuming_licenses = set()
    for i in range(len(data)):
        ip = data[i]["clientAddress"].split(":")[-1]
        if data[i]["licenseType"] == license_type:
            ips_consuming_licenses.add(ip)

    return list(ips_consuming_licenses)


def post_message(license_type, data, ip_addresses):
    msg = f'''Hi @all,

Squish's "{license_type}" licenses usage reached its maximum capacity.
Following are the IPs of hosts that are consuming these licenses:
'''

    missing_ip_names = []
    for i in range(len(data)):
        # Find which name corresponds to each IP
        keys = [k for k, v in ip_addresses.items() if data[i] in v]
        if keys:
            msg += f"{i+1}. {data[i]}: {keys[0]}\n"
        else:
            missing_ip_names.append(data[i])
            msg += f"{i+1}. {data[i]}\n"

    if missing_ip_names:
        msg += f"Please add a Machine's owner name for {[i for i in missing_ip_names]} here: https://docs.google.com/spreadsheets/d/1cDFtb2FZa-E7jVMErxqYqXRDk4r-V2KYUXsayM_-Wxk/edit?gid=0#gid=0"

    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
    bot_message = {'text': msg}
    http_obj = Http()

    response = http_obj.request(
        uri=chat_room_webhook,
        method='POST',
        headers=message_headers,
        body=json.dumps(bot_message),
    )
    return response


if __name__ == '__main__':
    ip_addresses = load_ip_addresses()  # <-- load from your merged CSV
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    usage = get_current_usage('tester')
    if usage >= 1:
        ips = get_ip_info('tester')
        post_message('tester', ips, ip_addresses)
        print(f"{dt_string} : successfully printed the tester license usage.")
    else:
        print(f"{dt_string} : Tester license usage is under the maximum limit.")
