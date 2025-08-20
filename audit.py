
import json
from flask_login import current_user
from extensions import db
from models import AuditLog

def log_action(action, entity, entity_id, payload=None):
    username = getattr(current_user, "username", "system")
    log = AuditLog(user=username, action=action, entity=entity, entity_id=entity_id, payload=json.dumps(payload or {}))
    db.session.add(log)
    db.session.commit()
