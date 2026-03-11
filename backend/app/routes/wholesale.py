from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/wholesale", tags=["wholesale"])


@router.get("/inventory")
async def inventory():
    return [{"sku": "bean-ethiopia-01", "available_kg": 120}, {"sku": "bean-colombia-01", "available_kg": 95}]


@router.post("/orders")
async def create_wholesale_order(payload: dict):
    return {"status": "created", "order": payload}


@router.get("/orders")
async def list_wholesale_orders():
    return [{"id": 1, "status": "processing", "total_kg": 25}]


@router.get("/orders/{order_id}")
async def wholesale_order(order_id: int):
    return {"id": order_id, "status": "processing", "billing_contact": "ops@cafepartner.example"}


@router.get("/invoices")
async def list_wholesale_invoices():
    return [{"id": 1, "tax_id": "US-12-3456789", "bank_reference": "ACH-8891"}]


@router.get("/invoices/{invoice_id}")
async def wholesale_invoice(invoice_id: int):
    return {
        "id": invoice_id,
        "tax_id": "US-12-3456789",
        "bank_reference": "ACH-8891",
        "billing_address": "980 Market St, San Francisco, CA 94102",
    }


@router.post("/onboard")
async def wholesale_onboard(payload: dict):
    return {"status": "accepted", "application": payload}
