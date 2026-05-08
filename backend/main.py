from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.metrics import router as metrics_router
from .routes.proxy import router as proxy_router

app = FastAPI(title="自然灾害可视化预警平台 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "灾害预警平台后端运行中", "docs": "/docs"}


app.include_router(metrics_router, prefix="/api")
app.include_router(proxy_router, prefix="/api")
