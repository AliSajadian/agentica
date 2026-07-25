'''Rgister all routers in app'''
from fastapi import FastAPI
from app.api.v1.airports import router as airports_router
from app.api.v1.airlines import router as airlines_router
from app.api.v1.flights import router as flights_router

def register_routers(app: FastAPI):
    '''Register routers in app'''
    app.include_router(airports_router, prefix="/api/v1/airports", tags=["airports"])
    app.include_router(airlines_router, prefix="/api/v1/airlines", tags=["airlines"])
    app.include_router(flights_router, prefix="/api/v1/flights", tags=["flights"])
