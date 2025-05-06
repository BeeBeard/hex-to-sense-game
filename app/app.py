from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import r_game, r_ws, r_dictionary

APP = FastAPI()
APP.mount("/static", StaticFiles(directory="app/static"), name="static")

APP.include_router(router=r_game)
APP.include_router(router=r_dictionary)
APP.include_router(router=r_ws)

if __name__ == "__main__":
    pass
