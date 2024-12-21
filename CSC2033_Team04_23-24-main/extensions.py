from flask_sqlalchemy import SQLAlchemy
import os
import certifi
from dotenv import load_dotenv
import pymongo
from flask_apscheduler import APScheduler

db = SQLAlchemy()
scheduler = APScheduler()

load_dotenv()

# Initiate databases
db = SQLAlchemy()
mdb = pymongo.MongoClient(os.getenv("MONGO_URI"), tlsCAFile=certifi.where())
