print("Running db init script")

from app import db
from models import init_db
init_db()

print("Initialized database")