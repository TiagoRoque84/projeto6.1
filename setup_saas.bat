@echo off
echo ========================================
echo   SETUP SAAS MULTI-TENANT
echo ========================================
echo.

echo [1/4] Criando migrations...
flask db migrate -m "Add multi-tenant support"
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Falha ao criar migrations
    echo Tentando inicializar o flask-migrate...
    flask db init
    flask db migrate -m "Add multi-tenant support"
)

echo.
echo [2/4] Aplicando migrations...
flask db upgrade

echo.
echo [3/4] Criando Super Admin e dados basicos...
flask init-data

echo.
echo [4/4] Criando tenant de demonstracao...
flask create-demo-tenant

echo.
echo ========================================
echo   SETUP CONCLUIDO!
echo ========================================
echo.
echo Proximo passo:
echo 1. Configure o arquivo HOSTS (veja TESTE_RAPIDO.md)
echo 2. Execute: python app.py
echo 3. Acesse: http://admin.local:5000/super-admin/login
echo.
echo Credenciais Super Admin:
echo   Usuario: superadmin
echo   Senha: admin123
echo.
pause
