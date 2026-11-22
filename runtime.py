import uuid
import platform
import subprocess
import psutil
import cpuinfo
import re
import os
import shutil
from pathlib import Path
import random
import string

def __uuid__(): return uuid.uuid4()

def run_command(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore').strip()
    except Exception: return ""

def __osinfo__():
    print(f"OS Version : {platform.system()} {platform.release()} ({platform.version()})")
    print(f"Kernel Version : {platform.release()} ({platform.machine()})")

def __cpuinfo__():
    info = cpuinfo.get_cpu_info()
    freq = psutil.cpu_freq()
    core = psutil.cpu_count(logical=False)
    thread = psutil.cpu_count(logical=True)
    print(f"CPU : {info.get('brand_raw', platform.processor)} ({freq.current:.2f} MHz {core} Core / {thread} Thread)")

def __raminfo__():
    ram = psutil.virtual_memory()
    os_name = platform.system()
    ddr_type = "Unknown"

    if os_name == "Windows":
        out = run_command("powershell -Command \"Get-ComInstance Win32_PhysicalMemory | Select-Object -ExpandProperty SMBIOSMemoryType\"")
        ddr_map = {
            "20": "DDR",
            "21": "DDR2",
            "24": "DDR3",
            "26": "DDR4",
            "34": "DDR5"
        }

        for line in out.splitlines():
            if line.strip() in ddr_map:
                ddr_type = ddr_map[line.strip()]
                break
    elif os_name == "Linux":
        out = run_command("dmidecode -t memory | grep -i 'Type:' | grep -v 'Unknown' | head -n 1")
        if out: ddr_type = out.split(":")[-1].strip()
    elif os_name == "Darwin":
        out = run_command("system_profiler SPMemoryDataType | grep 'Type:' | head -n 1")
        if out: ddr_type = out.split(":")[-1].strip()

    print(f"RAM : {ram.total / (1024**3):.2f} GB ({ddr_type})")

def __gpuinfo__():
    os_name = platform.system()
        
    if os_name == "Windows":
        out = run_command("powershell -Command \"Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name + ' | VRAM: ' + [math]::Round($_.AdapterRAM / 1MB) + ' MB' }\"")
        for line in out.splitlines():
            if line.strip(): print(f"{line.strip()}")
    elif os_name == "Linux":
        out = run_command("lspci | grep -i -E 'vga|3d|display'")
        for line in out.splitlines():
            print(f"GPU : {line.split(':')[-1].strip()}")
        vram = run_command("nvidia-smi --query-gpu=memory.total --format=csv,noheader")
        if vram: print(f"VRAM : {vram}")
    elif os_name == "Darwin":
        out = run_command("system_profiler SPDisplaysDataType | grep -E 'Chipset Model:|VRAM'")
        for line in out.splitlines(): print(f"{line.strip()}")

def __storageinfo__():
    os_name = platform.system()
        
    if os_name == "Windows":
        out = run_command("powershell -Command \"Get-PhysicalDisk | ForEach-Object { $_.FriendlyName + ' | ' + [math]::Round($_.Size / 1GB, 2) + ' GB | Tipe: ' + $_.MediaType }\"")
        for line in out.splitlines():
            if line.strip(): print(f"{line.strip()}")
    elif os_name == "Linux":
        out = run_command("lsblk -d -o NAME,MODEL,SIZE,ROTA | grep -v 'loop'")
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4:
                tipe = "SSD" if parts[-1] == "0" else "HDD"
                size = parts[-2]
                model = " ".join(parts[1:-2]) or parts[0]
                print(f"Storage : {model} ({tipe} {size})")
    elif os_name == "Darwin":
        out = run_command("diskutil list physical | grep '/dev/disk'")
        print(f"Storage : {out}")

def __computer_and_bios__():
    os_name = platform.system()
    
    if os_name == "Windows":
        model = run_command("powershell -Command \"(Get-CimInstance Win32_ComputerSystem).Model\"")
        bios = run_command("powershell -Command \"(Get-CimInstance Win32_BIOS).SMBIOSBIOSVersion\"")
        print(f"Computer : {model}")
        print(f"BIOS : {bios}")
    elif os_name == "Linux":
        model = run_command("cat /sys/devices/virtual/dmi/id/product_name")
        bios = run_command("cat /sys/devices/virtual/dmi/id/bios_version")
        print(f"Computer : {model or 'Need sudo access'}")
        print(f"BIOS : {bios or 'Need sudo access'}")
    elif os_name == "Darwin":
        model = run_command("sysctl -n hw.model")
        bios = run_command("system_profiler SPHardwareDataType | grep 'System Firmware Version' | awk -F': ' '{print $2}'")
        print(f"Computer : {model}")
        print(f"BIOS : {bios}")

def __battery__():
    batt = psutil.sensors_battery()
    if not batt: return "No battery detected"

    os_name = platform.system()
    seri = "Standard Battery"
    kapasitas = "Unknown Capacity"
    health_str = "Unknown Health"

    if os_name == "Windows":
        seri = run_command("powershell -Command \"(Get-CimInstance Win32_Battery).Name\"") or "Standard Battery"
        design = run_command("powershell -Command \"(Get-CimInstance -Namespace root\\wmi -ClassName BatteryStaticData).DesignedCapacity\"")
        full = run_command("powershell -Command \"(Get-CimInstance -Namespace root\\wmi -ClassName BatteryFullChargedCapacity).FullChargedCapacity\"")
        
        if design.isdigit() and int(design) > 0:
            kapasitas = f"{design} mWh"
            if full.isdigit():
                health = (int(full) / int(design)) * 100
                health_str = f"{health:.1f}%"

    elif os_name == "Linux":
        path = "/sys/class/power_supply/BAT0"
        seri = run_command(f"cat {path}/model_name") or "BAT0"
        design = run_command(f"cat {path}/energy_full_design") or run_command(f"cat {path}/charge_full_design")
        full = run_command(f"cat {path}/energy_full") or run_command(f"cat {path}/charge_full")
        
        if design.isdigit() and int(design) > 0:
            kapasitas = f"{int(design)/1000:.0f} mAh"
            if full.isdigit():
                health = (int(full) / int(design)) * 100
                health_str = f"{health:.1f}%"

    elif os_name == "Darwin":
        out = run_command("system_profiler SPPowerDataType")
        max_cap = re.search(r"Maximum Capacity:\s*(\d+%)", out)
        design_mah = re.search(r"Design Capacity \(mAh\):\s*(\d+)", out)
        seri = "Apple MacBook Battery"
        if design_mah:
            kapasitas = f"{design_mah.group(1)} mAh"
        if max_cap:
            health_str = max_cap.group(1)
    print(f"Battery : {seri} series - {kapasitas} ({health_str} Health)")

def __move__(old, new): shutil.move(old, new)
def __rename__(old, new): os.rename(old, new)

def __copy__(old, new):
    if Path(old).is_file(): shutil.copy2(old, new)
    if Path(old).is_dir(): shutil.copytree(old, new)

def __system__(command, *args, **kwargs):
    return subprocess.run(
        command,
        shell=True,
        check=True,
        capture_output=True,
        *args, **kwargs
    )

def __mkdir__(name_or_path, *args, **kwargs): Path(name_or_path).mkdir(exist_ok=True, parents=True, *args, **kwargs)

def __rmdir__(name_or_path, recursive=False, *args, **kwargs):
    p = Path(name_or_path)
    if recursive: shutil.rmtree(p, *args, **kwargs)
    else: p.rmdir()

def __touch__(name_or_path, *args, **kwargs): Path(name_or_path).touch(exist_ok=True, *args, **kwargs)
def __rmfile__(name_or_path, *args, **kwargs): Path(name_or_path).unlink(missing_ok=True, *args, **kwargs)
def __read__(path, *args, **kwargs): return Path(path).read_text(encoding='utf-8', *args, **kwargs)

def __write__(name_or_path, content):
    with open(name_or_path, "w", encoding='utf-8') as file:
        file.write(content)

def __append_file__(name_or_path, content):
    with open(name_or_path, "a", encoding='utf-8') as f:
        f.write(content)

def __listdir__(path, *args, **kwargs): return [items.name for items in Path(path).iterdir(*args, **kwargs)]

def __chdir__(to_path):
    try:
        os.chdir(to_path)
        return Path.cwd()
    except FileNotFoundError: print(f"Error: Directory '{to_path}' not found!")
    except NotADirectoryError: print(f"Error: '{to_path}' isn't a directory!")

def __exists__(name_or_path, *args, **kwargs):
    p = Path(name_or_path, *args, **kwargs)
    exists = p.exists()

    if not exists: print(f"Error: Path '{name_or_path}' doesn't exist!")
    return exists

def __random__(length):
    length = int(length)
    char = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choices(char, k=length))

def __seed__(length):
    length = int(length)
    return "".join(random.choices(string.digits, k=length))

def __choice__(start, end=None):
    if end is None:
        if hasattr(start, "elements"):
            if not start.elements: return None
            return random.choice(start.elements)
        elif isinstance(start, (list, tuple, str)):
            if not start: return None
            return random.choice(start)
        raise TypeError("choice() with 1 argument need array or string!")

    if isinstance(start, int) and isinstance(end, int):
        return random.randint(min(start, end), max(start, end))

    if isinstance(start, str) and isinstance(end, str) and len(start) == 1 and len(end) == 1:
        code_a, code_b = ord(start), ord(end)
        return chr(random.randint(min(code_a, code_b), max(code_a, code_b)))

    if hasattr(start, "elements") and isinstance(end, int):
        sliced = start.elements[:end + 1]
        if not sliced: return None
        return random.choice(sliced)

    raise TypeError("Unknown choice() argument combination")