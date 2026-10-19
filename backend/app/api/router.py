from fastapi import APIRouter
from app.api.ceso_routes import router as ceso_router
from app.api.cadd_routes import router as cadd_router
from app.api.msvs_routes import router as msvs_router
from app.api.simulation_routes import router as sim_router
from app.api.evaluation_routes import router as eval_router
from app.api.scenario_routes import router as scenario_router
from app.api.llm_routes import router as llm_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(ceso_router)
api_router.include_router(cadd_router)
api_router.include_router(msvs_router)
api_router.include_router(sim_router)
api_router.include_router(eval_router)
api_router.include_router(scenario_router)
api_router.include_router(llm_router)
