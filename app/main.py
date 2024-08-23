from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router


app = FastAPI()

app.include_router(api_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def read_root():
    '''
    Retourne la page d'accueil de l'application
    '''
    return FileResponse("app/templates/index.html")
