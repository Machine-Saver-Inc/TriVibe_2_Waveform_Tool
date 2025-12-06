from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import hardware

app = FastAPI(title="Modbus Dashboard")

# Mount routes
app.include_router(hardware.router)

# If we had static assets (css/js locally), we'd mount them here.
# app.mount("/static", StaticFiles(directory="app/static"), name="static")
