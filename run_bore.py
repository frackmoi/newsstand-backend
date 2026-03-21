import subprocess
import re
import time

def start_bore():
    print("Starting bore...")
    process = subprocess.Popen(
        ["npx.cmd", "-y", "bore-cli", "local", "8889", "--to", "bore.pub"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    url = None
    with open('bore_url.txt', 'w') as f:
        f.write('failed')

    for i in range(40):
        line = process.stdout.readline()
        if not line:
            time.sleep(0.5)
            continue
            
        print("OUT:", line.strip())
        match = re.search(r'bore\.pub:(\d+)', line)
        if match:
            url = f"http://bore.pub:{match.group(1)}"
            print(f"FOUND URL: {url}")
            with open('bore_url.txt', 'w') as f:
                f.write(url)
            break
            
    # keep it running
    process.wait()

if __name__ == "__main__":
    start_bore()
