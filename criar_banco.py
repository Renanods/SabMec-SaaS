from sabmec import db, app
from sabmec.models import *

with app.app_context():
    db.create_all()
