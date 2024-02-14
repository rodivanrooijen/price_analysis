#start_scraping.py
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/start_scraping", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("startscraping.html", {"request": request})

    