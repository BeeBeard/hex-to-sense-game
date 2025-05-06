from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import r_game, r_ws


APP = FastAPI()
APP.mount("/static", StaticFiles(directory="app/static"), name="static")

APP.include_router(router=r_game)
APP.include_router(router=r_ws)

if __name__ == "__main__":
    pass
