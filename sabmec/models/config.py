from sabmec import db

class ConfiguracaoOs(db.Model):
    __tablename__ = "config_ordens_servico"

    id = db.Column(db.Integer, primary_key=True)
    
    modelo_os = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    texto_rodape_os = db.Column(db.Text)