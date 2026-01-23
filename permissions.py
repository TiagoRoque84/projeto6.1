"""
Definição de permissões disponíveis no sistema
"""

AVAILABLE_PERMISSIONS = {
    'view_documents': 'Ver documentos',
    'edit_documents': 'Criar/editar documentos',
    'delete_documents': 'Excluir documentos',
    
    'view_companies': 'Ver empresas',
    'edit_companies': 'Criar/editar empresas',
    
    'view_employees': 'Ver funcionários',
    'edit_employees': 'Criar/editar funcionários',
    'delete_employees': 'Excluir funcionários',
    
    'view_customers': 'Ver clientes',
    'edit_customers': 'Criar/editar clientes',
    
    'view_reports': 'Ver relatórios e dashboard',
    'manage_users': 'Gerenciar usuários',
    
    'view_scheduling': 'Ver agendamentos',
    'edit_scheduling': 'Criar/editar agendamentos',
    
    'view_epi': 'Ver EPIs',
    'edit_epi': 'Criar/editar EPIs',
    
    'view_pdv': 'Ver caixa/PDV',
    'edit_pdv': 'Registrar vendas no PDV',
}

# Permissões padrão para novos usuários do tipo 'user'
DEFAULT_USER_PERMISSIONS = {
    'view_documents': True,
    'view_companies': True,
    'view_employees': True,
    'view_customers': True,
    'view_reports': True,
}
