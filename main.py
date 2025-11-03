from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import api_router
from middleware import exception_handlers
from src.db.database import SessionLocal, db_session_context

def create_application() -> FastAPI:

    app = FastAPI(
        title="Jira Webhook Receiver",
        description="A service to receive and process Jira webhook notifications",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    exception_handlers.register_exception_handlers(app)

    @app.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        db = SessionLocal()
        token = db_session_context.set(db)
        try:
            response = await call_next(request)
        finally:
            db_session_context.reset(token)
            db.close()
        return response

    return app

app = create_application()

if __name__ == "__main__":
    #uvicorn main:app --reload --host="0.0.0.0" --port=8001
    #redis-cli -h 10.146.12.34 -p 31379 -a neuadminredis
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
