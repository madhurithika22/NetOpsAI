import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.models.ceso_models import NetworkState
from app.ceso.service import ceso_service

router = APIRouter(prefix="/ceso", tags=["CESO Layer"])

@router.get("/state", response_model=NetworkState)
def get_network_state():
    """Retrieve current normalized network state snapshot."""
    return ceso_service.get_latest_state()

@router.post("/collect", response_model=NetworkState)
def collect_network_state():
    """Trigger immediate telemetry collection and normalization."""
    return ceso_service.collect_and_normalize()

@router.get("/stream")
async def stream_network_state(request: Request, interval: float = 2.0):
    """
    Server-Sent Events (SSE) endpoint emitting periodic NetworkState updates.
    Handles client disconnects gracefully and runs asynchronously without blocking.
    """
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                state = ceso_service.get_latest_state()
                data_json = state.model_dump_json()
                yield f"event: network_state\ndata: {data_json}\n\n"
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
