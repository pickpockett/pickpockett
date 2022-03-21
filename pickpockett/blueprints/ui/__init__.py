from flask import Blueprint

from . import add, edit, index, settings

bp = Blueprint("ui", __name__)
bp.register_blueprint(add.bp)
bp.register_blueprint(edit.bp)
bp.register_blueprint(index.bp)
bp.register_blueprint(settings.bp)
