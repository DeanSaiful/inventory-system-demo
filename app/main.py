from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.core.database import Base, engine
from app.routers import profile
from app.routers import reports



# Routers
from app.routers import auth, request, stock, returns, users


# Models (ALIAS request model)
from app.models import user, component, request as request_model

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates

# Create DB tables
Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(auth.router)
app.include_router(request.router)
app.include_router(stock.router)
app.include_router(returns.router)
app.include_router(users.router)
app.include_router(profile.router)
app.include_router(reports.router)

