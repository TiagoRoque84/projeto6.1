# init_financial_data.py
"""
Script para inicializar dados básicos do sistema financeiro
"""

from app import create_app
from extensions import db
from models_financial import PaymentMethod, FinancialCategory

app = create_app()

with app.app_context():
    print("Inicializando dados financeiros...")
    
    # Formas de Pagamento
    payment_methods = [
        {'name': 'Dinheiro', 'icon': '💵', 'description': 'Pagg em espécie'},
        {'name': 'PIX', 'icon': '📱', 'description': 'Transferência instantânea'},
        {'name': 'Transferência Bancária', 'icon': '🏦', 'description': 'TED/DOC'},
        {'name': 'Cartão de Crédito', 'icon': '💳', 'description': 'Pagamento com cartão de crédito'},
        {'name': 'Cartão de Débito', 'icon': '💳', 'description': 'Pagamento com cartão de débito'},
        {'name': 'Boleto', 'icon': '📄', 'description': 'Boleto bancário'},
        {'name': 'Cheque', 'icon': '📝', 'description': 'Pagamento em cheque'},
    ]
    
    for pm_data in payment_methods:
        existing = PaymentMethod.query.filter_by(name=pm_data['name']).first()
        if not existing:
            pm = PaymentMethod(**pm_data)
            db.session.add(pm)
            print(f"  ✓ Forma de pagamento: {pm_data['name']}")
    
    # Categorias de Receita
    receita_categories = [
        {'name': 'Mensalidades', 'type': 'receita', 'color': '#48bb78', 'icon': '💰', 'description': 'Mensalidades de clientes'},
        {'name': 'Taxa de Setup', 'type': 'receita', 'color': '#4299e1', 'icon': '⚙️', 'description': 'Taxa de implantação'},
        {'name': 'Upgrade de Plano', 'type': 'receita', 'color': '#9f7aea', 'icon': '📈', 'description': 'Upgrade para plano superior'},
        {'name': 'Serviços Extras', 'type': 'receita', 'color': '#ed8936', 'icon': '🎁', 'description': 'Serviços adicionais'},
        {'name': 'Consultoria', 'type': 'receita', 'color': '#38b2ac', 'icon': '💼', 'description': 'Serviços de consultoria'},
        {'name': 'Outras Receitas', 'type': 'receita', 'color': '#667eea', 'icon': '📊', 'description': 'Outras fontes de receita'},
    ]
    
    for cat_data in receita_categories:
        existing = FinancialCategory.query.filter_by(name=cat_data['name'], type='receita').first()
        if not existing:
            cat = FinancialCategory(**cat_data)
            db.session.add(cat)
            print(f"  ✓ Categoria receita: {cat_data['name']}")
    
    # Categorias de Despesa
    despesa_categories = [
        {'name': 'Infraestrutura', 'type': 'despesa', 'color': '#e53e3e', 'icon': '🖥️', 'description': 'Servidor, domínio, hospedagem'},
        {'name': 'Marketing', 'type': 'despesa', 'color': '#d69e2e', 'icon': '📢', 'description': 'Anúncios, campanhas'},
        {'name': 'Desenvolvimento', 'type': 'despesa', 'color': '#805ad5', 'icon': '💻', 'description': 'Equipe de desenvolvimento'},
        {'name': 'Suporte', 'type': 'despesa', 'color': '#319795', 'icon': '🎧', 'description': 'Equipe de suporte'},
        {'name': 'Impostos', 'type': 'despesa', 'color': '#c53030', 'icon': '📑', 'description': 'Impostos e taxas'},
        {'name': 'Salários', 'type': 'despesa', 'color': '#dd6b20', 'icon': '👥', 'description': 'Folha de pagamento'},
        {'name': 'Contabilidade', 'type': 'despesa', 'color': '#718096', 'icon': '📘', 'description': 'Serviços contábeis'},
        {'name': 'Escritório', 'type': 'despesa', 'color': '#4a5568', 'icon': '🏢', 'description': 'Aluguel, contas'},
        {'name': 'Ferramentas/Software', 'type': 'despesa', 'color': '#2d3748', 'icon': '🔧', 'description': 'Softwares e ferramentas'},
        {'name': 'Outras Despesas', 'type': 'despesa', 'color': '#1a202c', 'icon': '📉', 'description': 'Outras saídas'},
    ]
    
    for cat_data in despesa_categories:
        existing = FinancialCategory.query.filter_by(name=cat_data['name'], type='despesa').first()
        if not existing:
            cat = FinancialCategory(**cat_data)
            db.session.add(cat)
            print(f"  ✓ Categoria despesa: {cat_data['name']}")
    
    db.session.commit()
    print("\n✅ Dados financeiros inicializados com sucesso!")
    print(f"   - {len(payment_methods)} formas de pagamento")
    print(f"   - {len(receita_categories)} categorias de receita")
    print(f"   - {len(despesa_categories)} categorias de despesa")
