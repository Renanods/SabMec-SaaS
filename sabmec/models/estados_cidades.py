from sabmec import db, login_manager

class Estado(db.Model):
    __tablename__ = "estados"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    uf = db.Column(db.String(2), nullable=False, unique=True)
    codigo_ibge = db.Column(db.Integer, nullable=False, unique=True)

    # Relacionamentos
    cidades = db.relationship("Cidade", back_populates="estado")

    def __repr__(self):
        return self.nome

class Cidade(db.Model):
    __tablename__ = "cidades"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    estado_id = db.Column(db.Integer, db.ForeignKey("estados.id"), nullable=False)
    codigo_ibge = db.Column(db.Integer, nullable=False, unique=True)

    # Relacionamentos

    estado = db.relationship("Estado", back_populates="cidades")

    @classmethod
    def buscar_por_estado(self, estado_id):
        return self.query.filter_by(estado_id=estado_id).all()
    
    def __repr__(self):
        return self.nome

