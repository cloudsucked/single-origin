from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/sensors", tags=["sensors"])


@router.post("/data")
async def sensor_data(payload: dict):
    return {"ingested": True, "payload": payload}


@router.get("/status")
async def sensor_status():
    return {"roaster-001": "online", "roaster-002": "maintenance"}


@router.get("/devices")
async def sensor_devices():
    return [
        {"id": "roaster-001", "serial": "SO-AX91-2221", "firmware": "1.8.2"},
        {"id": "roaster-002", "serial": "SO-BQ11-7814", "firmware": "1.7.9"},
    ]
