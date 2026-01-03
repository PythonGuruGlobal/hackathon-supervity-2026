# Simple script that acts as a bridge if we wanted to serve static files
# For this tasks, the user requested "Backend Proxy: Connect React UI to FastAPI"
# Since React typically runs on 3000 and FastAPI on 8000, this could just be a CORS configuration or a simple static file server.
# Given FastAPI is used, we can just mount the static files there if built.
# However, to simulate a proxy in a separate file as requested:

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.vectra_api import app as api_app

app = FastAPI()

# Mount API
app.mount("/api", api_app)

# Serve Frontend (assuming build exists, otherwise just placeholder)
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
