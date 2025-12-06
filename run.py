import os
import sys
import subprocess
import platform

def is_docker():
    path = '/.dockerenv'
    return os.path.exists(path)

def setup_venv():
    if is_docker():
        print("Running in Docker, skipping venv setup.")
        return

    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment in {venv_dir}...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
    
    # Install requirements
    pip_cmd = os.path.join(venv_dir, "Scripts" if os.name == "nt" else "bin", "pip")
    print("Installing requirements...")
    subprocess.check_call([pip_cmd, "install", "-r", "requirements.txt"])

def run_app():
    if is_docker():
        print("Detected Docker environment.")
        os.environ["MODBUS_MODE"] = "mock" # Default to mock in docker unless overridden
    else:
        print("Detected Local environment.")
        # Check if we want to force mock
        if "MODBUS_MODE" not in os.environ:
             print("Defaulting to Real Hardware mode (try accessing COM ports).")
             os.environ["MODBUS_MODE"] = "real"

    python_cmd = sys.executable
    if not is_docker():
        python_cmd = os.path.join("venv", "Scripts" if os.name == "nt" else "bin", "python")

    print(f"Starting App with MODBUS_MODE={os.environ['MODBUS_MODE']}")
    subprocess.call([python_cmd, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

if __name__ == "__main__":
    setup_venv()
    run_app()
