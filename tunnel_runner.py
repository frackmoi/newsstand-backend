wimport subprocess
import re
import time

def start_tunnel():
    print("Starting tunnel...")
    process = subprocess.Popen(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:8889", "nokey@localhost.run"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    url = None
    # Wait for URL to appear in output
    for i in range(20):
        line = process.stdout.readline()
        if not line:
            time.sleep(0.5)
            continue
            
        print("OUT:", line.strip())
        match = re.search(r'(https://[a-zA-Z0-9.-]+\.lhr\.life)', line)
        if match:
            url = match.group(1)
            print(f"FOUND URL: {url}")
            break
        match2 = re.search(r'([a-zA-Z0-9.-]+\.serveo\.net)', line)
        if match2:
            url = f"https://{match2.group(1)}"
            print(f"FOUND URL: {url}")
            break
            
    with open('tunnel_url.txt', 'w') as f:
        f.write(url if url else 'failed')
        
    # keep it running
    process.wait()

if __name__ == "__main__":
    start_tunnel()
