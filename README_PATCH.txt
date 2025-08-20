
Para ativar os cards de Toxicológico sem mexer no seu dashboard atual,
você pode acessar a rota /dash após registrar o blueprint no app.py:

from blueprints.dash.routes import dash_bp
app.register_blueprint(dash_bp)

Se preferir incorporar os cards na sua página atual de dashboard,
copie o grid de cards (templates/dashboard.html) para o seu arquivo de dashboard.
