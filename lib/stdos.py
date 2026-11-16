import os
import uuid
import shutil
import subprocess
from pathlib import Path

def __move__(old_path, new_path):
    try: shutil.move(old_path, new_path)
    except Exception as e: return f"{e}"

def __rename__(old_path, new_path):
    try: os.rename(old_path, new_path)
    except Exception as e: return f"{e}"

def __copy__(old_path, new_path):
    try: shutil.copy(old_path, new_path)
    except Exception as e: return f"{e}"

def __system__(*args, **kwargs):
    try:
        full_command = " && ".join(str(arg) for arg in args)
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            **kwargs
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e: return f"{e.stderr}"
    except Exception as e: return f"{e}"

def __mkdir__(name, *args, **kwargs): 
    try: os.makedirs(name, *args, **kwargs)
    except Exception as e: return str(e)

def __rmdir__(name, *args, **kwargs): 
    try: os.removedirs(name)
    except Exception as e: return str(e)

def __touch__(name, *args, **kwargs):
    try: Path(name).touch(*args, **kwargs)
    except Exception as e: return f"{e}"

def __rmfile__(name, *args, **kwargs):
    try: Path(name).unlink(*args, **kwargs)
    except Exception as e: return f"{e}"

def __read__(name, *args, **kwargs):
    try:
        path = Path(name)
        if not path.is_file(): return f"Error: File {name} not found!"

        content = path.read_text(*args, **kwargs)
        return content
    except Exception as e: return str(e)

def __cd__(path):
    try:
        os.chdir(path)
        return os.getcwd()
    except FileNotFoundError: return f"Error: Directory {path} not found!"
    except Exception as e: return str(e)

def __ls__(path=".", *args, **kwargs):
    try:
        items = os.listdir(path)
        return items
    except FileNotFoundError: return f"Error: Path {path} not found!"
    except Exception as e: return str(e)

def __write__(path, content):
    try: Path(path).write_text(str(content), encoding="utf-8")
    except Exception as e: return str(e)

def __append_file__(path, content):
    try:
        with open(path, 'a') as f:
            f.write(str(content) + "\n")
    except Exception as e: return str(e)

def __getpwd__(): return os.getcwd()
def __gethome__(): return str(Path.home())
def __getuuid__(): return str(uuid.uuid4())