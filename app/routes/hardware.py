from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.services.modbus_manager import ModbusService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
modbus = ModbusService()

@router.get("/ports", response_class=JSONResponse)
async def get_ports():
    return modbus.get_ports()

@router.post("/connect")
async def connect(request: Request, port: str = Form(...), slave_id: int = Form(1)):
    success = modbus.connect(port, int(slave_id))
    
    # Return the updated connection bar or dashboard via HTMX
    # For simplicity, we just reload the main dashboard content if successful
    if success:
        return await dashboard_view(request)
    else:
        return HTMLResponse(f"<div class='text-red-500 font-bold'>Connection Failed to {port}</div>")

@router.post("/disconnect")
async def disconnect(request: Request):
    modbus.disconnect()
    return await dashboard_view(request)

@router.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    if modbus.connection_status.startswith("Connected"):
        data = modbus.read_data()
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "connected": True,
            "status": modbus.connection_status,
            "data": data
        })
    else:
        ports = modbus.get_ports()
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "connected": False,
            "status": modbus.connection_status,
            "ports": ports
        })

@router.get("/api/data/stream")
async def stream_data():
    """Returns JSON for charts to consume"""
    data = modbus.read_stream_data()
    return JSONResponse(data if data else {})

@router.post("/api/settings/update")
async def update_setting(
    request: Request,
    register: int = Form(...),
    value: int = Form(...)
):
    success = modbus.write_setting(register, value)
    if success:
        # Return the new value as a simple text string to swap into the UI
        return HTMLResponse(str(value)) 
    else:
        return HTMLResponse("Err", status_code=500)
