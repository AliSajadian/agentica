'''Rgister all routers in app'''
from fastapi import FastAPI
from .sessions import router


def register_routers(app: FastAPI):
    '''Register routers in app'''
    app.include_router(router, prefix="/api/v1", tags=["sessions"])
