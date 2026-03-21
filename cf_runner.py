import subprocess
import urllib.request
import re
import time

def start_cf():
    print("Downloading cloudflared.exe...")
    urllib.request.urlretrieve("https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe", "cloudflared.exe")

    print("Starting cloudflared...")
    p = subprocess.Popen(["cloudflared.exe", "tunnel", "--url", "http://localhost:8889"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore')

    url = None
    with open("cf_url.txt", "w") as f: f.write("failed")

    for i in range(100):
        line = p.stdout.readline()
        if not line:
            time.sleep(0.2)
            continue
        print("OUT:", line.strip())
        match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
        if match:
            url = match.group(1)
            print("FOUND URL:", url)
            with open("cf_url.txt", "w") as f: f.write(url)
            break

    while True:
        time.sleep(1)

if __name__ == "__main__":
    start_cf()
