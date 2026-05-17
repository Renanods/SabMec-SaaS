from sabmec import db


class Veiculo(db.Model):
    __tablename__ = "veiculos"

    id = db.Column(db.Integer, primary_key=True)

    pessoa_id = db.Column(
        db.Integer,
        db.ForeignKey("pessoas.id"),
        nullable=False,
    )

    placa = db.Column(db.String(10), nullable=False, unique=True)
    marca = db.Column(db.String(60), nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    ano_fabricacao = db.Column(db.Integer)
    ano_modelo = db.Column(db.Integer)
    cor = db.Column(db.String(50))
    chassi = db.Column(db.String(30))
    renavam = db.Column(db.String(20))
    observacao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)

    pessoa = db.relationship("Pessoa", back_populates="veiculos")
