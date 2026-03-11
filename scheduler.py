import os
import platform
import subprocess
from pathlib import Path
import json

base_dir = Path(__file__).parent
config_path = base_dir / "config.json"
script_path = base_dir / "organizer.py"

with open(config_path) as f:
    config = json.load(f)

time = config["schedule_time"]

os_name = platform.system()

print(f"Detected OS {os_name}")



if os_name == "Windows":
    cmd = f'schtasks /create /sc daily /st {time} /tn "AutoBackup" /tr "python {script_path}" /f'
    subprocess.run(cmd, shell=True)
    print("Windows Task Scheduler configured")


elif os_name in ["Linux", "Darwin"]:
    hour, minute = time.split(":")
    cron_job = f"{minute} {hour} * * * python3 {script_path}"

    subprocess.run(f'(crontab -l 2>/dev/null; echo "{cron_job}") | crontab -', shell=True)
    print("Cron job installed")

else:
    print(" Unsupported OS")