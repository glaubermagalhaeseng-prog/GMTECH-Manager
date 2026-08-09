"""Formatação brasileira de valores e números."""


def moeda(valor) -> str:
    """
    Formata número como Real brasileiro.
    Ex.: 25000.5 -> 25.000,50
    """
    try:
        if valor is None or valor == "":
            valor = 0
        n = float(valor)
    except (TypeError, ValueError):
        n = 0.0

    texto = f"{n:,.2f}"
    # 25,000.50 (US) -> 25.000,50 (BR)
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def moeda_rs(valor) -> str:
    """Com prefixo R$."""
    return f"R$ {moeda(valor)}"


def numero_br(valor, casas: int = 2) -> str:
    """Número com vírgula decimal (sem R$)."""
    try:
        if valor is None or valor == "":
            valor = 0
        n = float(valor)
    except (TypeError, ValueError):
        n = 0.0
    texto = f"{n:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
