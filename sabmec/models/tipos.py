from sabmec import db

class Status(db.Model):
    __tablename__ = 'status'

    id = db.Column(db.Integer, primary_key=True)
    situacao = db.Column(db.String(25), nullable=False, unique=True)

