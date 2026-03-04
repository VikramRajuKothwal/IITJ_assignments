# cloudburst.py
import psutil
import subprocess
import time
import tempfile
import os

PROJECT_ID = "vcc-assignment-3-m25ai2033"
ZONE = "asia-south1-a"
INSTANCE_NAME = "autoscaled-vm-vikram"
MACHINE_TYPE = "e2-micro"
IMAGE_FAMILY = "ubuntu-2204-lts"
IMAGE_PROJECT = "ubuntu-os-cloud"
THRESHOLD = 75.0
CHECK_INTERVAL = 30  # seconds
gcp_instance_exists = False

def get_resource_usage():
    cpu = psutil.cpu_percent(interval=2)
    mem = psutil.virtual_memory().percent
    return cpu, mem

def instance_exists():
    result = subprocess.run(
        ["gcloud", "compute", "instances", "describe", INSTANCE_NAME,
         "--zone", ZONE, "--project", PROJECT_ID],
        capture_output=True
    )
    return result.returncode == 0

def create_gcp_instance():
    print(f"[ALERT] Usage > {THRESHOLD}%. Scaling out to GCP...")

    startup_script = """#!/bin/bash
cat << 'EOF' > /home/app.py
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>Auto-Scaled GCP Instance is Running!</h1><BR><h2>VCC assignment 3 completed by Vikram Raju Kothwal")
    def log_message(self, format, *args):
        pass

server = HTTPServer(('0.0.0.0', 8085), Handler)
server.serve_forever()
EOF
python3 /home/app.py &
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(startup_script)
        tmp_path = f.name

    subprocess.run([
    "gcloud", "compute", "instances", "create", INSTANCE_NAME,
    "--project", PROJECT_ID,
    "--zone", ZONE,
    "--machine-type", MACHINE_TYPE,
    "--image-family", IMAGE_FAMILY,
    "--image-project", IMAGE_PROJECT,
    "--tags", "http-server",
    "--no-service-account",
    "--no-scopes",
    "--metadata-from-file", f"startup-script={tmp_path}"
    ])


    os.unlink(tmp_path)
    result = subprocess.run([
        "gcloud", "compute", "instances", "describe", INSTANCE_NAME,
        "--zone", ZONE,
        "--project", PROJECT_ID,
        "--format=get(networkInterfaces[0].accessConfigs[0].natIP)"
    ], capture_output=True, text=True)

    external_ip = result.stdout.strip()
    print(f"[INFO] GCP instance '{INSTANCE_NAME}' created successfully.")
    print(f"[INFO] Access your webapp in new GCP instance at: http://{external_ip}:8085")


def delete_gcp_instance():
    print(f"[INFO] Usage dropped below {THRESHOLD}% CPU threshold. Scaling in — deleting GCP instance...")
    subprocess.run([
        "gcloud", "compute", "instances", "delete", INSTANCE_NAME,
        "--zone", ZONE, "--project", PROJECT_ID, "--quiet"
    ])
    print(f"[INFO] GCP instance '{INSTANCE_NAME}' deleted.")

if __name__ == "__main__":
    print("Starting auto-scaling monitor...")
    while True:
        cpu, mem = get_resource_usage()
        print(f"CPU: {cpu}% | Memory: {mem}%")
        exists = instance_exists()

        if (cpu > THRESHOLD or mem > THRESHOLD) and not exists:
            create_gcp_instance()
        elif cpu < THRESHOLD and mem < THRESHOLD and exists:
            delete_gcp_instance()
        else:
            if exists:
                print(f"[OK] Usage > {THRESHOLD}% but GCP instance already active. No duplicate created.")
            else:
                print(f"[OK] Within threshold. No GCP instance needed.")


        time.sleep(CHECK_INTERVAL)
