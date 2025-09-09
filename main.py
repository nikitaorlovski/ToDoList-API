from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from admin.admin import init_admin
from api.auth import router as auth_router
from api.tasks import router as task_router
from api.views import router as view_router
from db.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    print("Tables Created")
    yield

BASE_DIR   = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(debug=True, lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(auth_router)
app.include_router(task_router)
app.include_router(view_router)
init_admin(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)