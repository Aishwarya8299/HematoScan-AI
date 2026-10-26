"""
Version 1 API router aggregator.

New route modules (auth, technician, doctor) will be included here as we
build each step — keeping a single mount point in main.py.
"""

from fastapi import APIRouter

from app.api.v1 import auth, doctor, system, technician

api_v1_router = APIRouter()
api_v1_router.include_router(system.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(technician.router)
api_v1_router.include_router(doctor.router)
