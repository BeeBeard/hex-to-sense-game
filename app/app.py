from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import r_game, r_ws, r_dictionary
from app.config import CONFIG

APP = FastAPI(root_path=CONFIG.api.path)
APP.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

APP.mount("/static", StaticFiles(directory="app/static"), name="static")

APP.include_router(router=r_game)
APP.include_router(router=r_dictionary)
APP.include_router(router=r_ws)

if __name__ == "__main__":
    pass
