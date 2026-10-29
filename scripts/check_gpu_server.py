"""모델 서버 띄우기 전에 GPU 서버 상태 확인 (디스크/메모리/GPU/Docker/포트)"""
import shutil
import socket
import subprocess


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def port_free(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


free = shutil.disk_usage(".").free / 1e9
print(f"disk free : {free:.0f} GB {'(OK)' if free > 30 else '(triton 이미지 ~15GB, 30GB 이상 권장)'}")

try:
    import psutil
    print(f"memory    : {psutil.virtual_memory().total / 1e9:.0f} GB")
except ImportError:
    pass

r = run(["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,compute_cap", "--format=csv,noheader"])
print("gpu       :", r.stdout.strip().replace("\n", "\n            ") if r and r.returncode == 0 else "not found")

r = run(["docker", "info", "--format", "{{.ServerVersion}}"])
if r is None:
    print("docker    : not installed")
elif r.returncode != 0:
    print("docker    : not running or permission denied (sudo usermod -aG docker $USER)")
else:
    print("docker    :", r.stdout.strip())

for name, port in [("api", 8080), ("triton", 8000), ("triton-metrics", 8002), ("vllm", 8100)]:
    print(f"port {port:<5}: {'free' if port_free(port) else 'in use'} ({name})")
