# Modbus RTU Dashboard

A Python-native dashboard to control RS485 sensors, visualize vibration data, and manage settings.

## Features
- **Real-time Visualization**: High-speed charting with Apache ECharts.
- **Hardware Control**: Direct Modbus RTU communication via `minimalmodbus`.
- **Cross-Platform**: logical handling for Windows (Local) and Linux (Production/Docker).

## Getting Started

### Windows (Local Development)
Pre-requisites: Python 3.11+

1. Run the utility script:
   ```powershell
   python run.py
   ```
   This will automatically create a virtual environment, install dependencies, and start the server.

2. Open browser at `http://localhost:8000`

### Linux / Docker
If running in a container, the app defaults to "Mock Mode" since access to host COM ports needs privileged flags.

```bash
docker build -t modbus-dash .
docker run -p 8000:8000 modbus-dash
```

To run with REAL hardware on Linux Docker, you must pass the device:
```bash
docker run --device=/dev/ttyUSB0 -e MODBUS_MODE=real -p 8000:8000 modbus-dash
```
