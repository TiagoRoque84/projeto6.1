import os, socket
ENC = "cp860"  # acentos PT-BR em muitas térmicas

def _encode(s: str) -> bytes:
    return (s or "").encode(ENC, errors="ignore")

def _cut() -> bytes:
    return b"\x1d\x56\x41\x10"  # corte parcial ESC/POS

def build_ticket_lines(title: str, header_lines, cols: int, fields, ask_signature=False):
    # Monta um ticket simples como lista de linhas (texto puro).
    cols = int(cols or 40)
    sep = "-" * cols
    center = lambda t: t.center(cols)
    lines = []
    for h in (header_lines or []):
        lines.append(center(h))
    lines += [sep, center(title), sep]
    for k,v in (fields or []):
        if v is None or v == "":
            v = "-"
        k = str(k)
        v = str(v)
        base = f"{k}: {v}"
        if len(base) <= cols:
            lines.append(base)
        else:
            lines.append(f"{k}:")
            while v:
                lines.append(v[:cols])
                v = v[cols:]
    lines.append(sep)
    if ask_signature:
        lines += ["Assinatura:".ljust(cols), "", "_" * int(cols*0.6)]
        lines.append(sep)
    lines.append("")
    return lines

def _to_escpos_bytes(lines):
    INIT = b"\x1b\x40"
    bbody = b"".join([_encode(l) + b"\n" for l in (lines or [])])
    return INIT + bbody + _cut()

def print_ticket(lines):
    """Imprime via TCP (host/port) ou via Spooler do Windows (nome da impressora)."""
    host = os.getenv("TICKET_PRINTER_HOST")
    port = int(os.getenv("TICKET_PRINTER_PORT","9100"))
    name = os.getenv("TICKET_PRINTER_NAME")  # ex.: EPSON TM-T20 ReceiptE4
    raw = _to_escpos_bytes(lines)

    if host:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, port))
            s.sendall(raw)
            s.close()
            return True, None
        except Exception as e:
            return False, str(e)

    if name:
        try:
            import win32print
            h = win32print.OpenPrinter(name)
            try:
                job = win32print.StartDocPrinter(h, 1, ("Ticket", None, "RAW"))
                win32print.StartPagePrinter(h)
                win32print.WritePrinter(h, raw)
                win32print.EndPagePrinter(h)
                win32print.EndDocPrinter(h)
            finally:
                win32print.ClosePrinter(h)
            return True, None
        except Exception as e:
            return False, str(e)

    return False, "Nenhuma impressora configurada. Defina TICKET_PRINTER_NAME (USB) ou TICKET_PRINTER_HOST."
