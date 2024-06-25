from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dotenv import dotenv_values
from pymongo import MongoClient
from routers import tour, reservation

# https:stackoverflow.com/questions/45732838/authentication-failed-to-connect-to-mongodb-using-pymongo
# https://www.mongodb.com/resources/languages/pymongo-tutorial

config = dotenv_values(".env")

USR = config['USR']
PWD = config['PWD']
HOST = config['HOST']
DBNAME = config['DB_NAME']
URI = "mongodb://" + USR + ":" + PWD + "@" + \
          HOST + "/test_db?authSource=admin&retryWrites=true&w=majority"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_db_client():
    app.mongodb_client = MongoClient(URI)
    app.database = app.mongodb_client[DBNAME]

    # if database not exist, reload demo data
    if DBNAME not in app.mongodb_client.list_database_names():
        from restart import load_data
        load_data(app.database)

    # to restart demo data, uncomment this line
    # wait for application to restart, uncomment it again
    # app.mongodb_client.drop_database(DBNAME)

@app.on_event("shutdown")
def shutdown_db_client():
    app.mongodb_client.close()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name='index.html')

app.include_router(tour.router, tags=["tours"], prefix="/tours")
app.include_router(reservation.router, tags=["reservations"], prefix="/reservations")