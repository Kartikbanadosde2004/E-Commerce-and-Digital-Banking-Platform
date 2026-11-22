from app import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer)
    action = db.Column(db.String, nullable=False)
    entity_type = db.Column(db.String)
    entity_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now())