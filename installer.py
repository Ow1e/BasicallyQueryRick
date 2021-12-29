from app import db
import os

os.mkdir("sqlite")
db.create_all()
