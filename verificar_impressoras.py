# verificar_impressoras.py
import win32print

try:
    # Pega a lista de todas as impressoras instaladas
    printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)

    print("--- Impressoras encontradas no Windows ---")
    if not printers:
        print("Nenhuma impressora encontrada.")
    else:
        for i, printer_info in enumerate(printers):
            # O nome que precisamos está na posição 2 da tupla de informações
            printer_name = printer_info[2]
            print(f"{i + 1}: '{printer_name}'")

    print("\nCopie o nome exato (sem as aspas simples) de uma das impressoras acima e cole no seu arquivo .env")
    print("Exemplo: TICKET_PRINTER_NAME=EPSON TM-T20 Receipt")

except Exception as e:
    print(f"Ocorreu um erro ao tentar listar as impressoras: {e}")
    print("Verifique se a biblioteca pywin32 está instalada corretamente: pip install pywin32")