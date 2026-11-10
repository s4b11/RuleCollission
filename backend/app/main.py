from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .api import agent_internal, auth, ops, public, studio
from .db import Base, SessionLocal, engine
from .seed.demo import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    if config.SEED_DEMO:
        with SessionLocal() as db:
            seed_if_empty(db)
    yield


app = FastAPI(title="RuleCollision", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

for module in (auth, public, ops, studio, agent_internal):
    app.include_router(module.router)


@app.get("/health")
def health():
    return {"ok": True}
