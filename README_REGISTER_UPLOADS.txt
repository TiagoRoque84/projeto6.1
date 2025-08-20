
No app.py (dentro de create_app()), registre o blueprint de uploads:

from blueprints.uploads.routes import uploads_bp
app.register_blueprint(uploads_bp)

Agora todo arquivo salvo em <root>/uploads/... abre via URL /uploads/<path>.
Ex.: se save_file retornar 'func_docs/abc.pdf', a URL será /uploads/func_docs/abc.pdf
