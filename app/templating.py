from fastapi.templating import Jinja2Templates

from app.formatadores import moeda, moeda_rs, numero_br

templates = Jinja2Templates(directory="app/templates")

templates.env.filters["moeda"] = moeda
templates.env.filters["moeda_rs"] = moeda_rs
templates.env.filters["numero_br"] = numero_br
