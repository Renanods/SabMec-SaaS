from datetime import datetime
from sabmec import db

# IDs de status de agendamento na tabela Status
STATUS_AGENDADO_ID  = 6
STATUS_CONCLUIDO_ID = 7
STATUS_CANCELADO_ID = 3

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('pessoas.id'), nullable=False, index=True)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=False, index=True)
    
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    
    problema_relatado = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=True, default=STATUS_AGENDADO_ID, index=True)
    
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=True)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    cliente = db.relationship('Pessoa', foreign_keys=[cliente_id])
    veiculo = db.relationship('Veiculo', foreign_keys=[veiculo_id])
    ordem_servico = db.relationship('OrdemServico', foreign_keys=[ordem_servico_id])
    status = db.relationship('Status', foreign_keys=[status_id])

    # Índice composto para facilitar a busca por data/hora
    __table_args__ = (
        db.Index('idx_agendamento_data_hora', 'data', 'hora'),
    )
