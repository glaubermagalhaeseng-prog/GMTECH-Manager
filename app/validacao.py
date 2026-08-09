"""Helpers de validação de formulários."""

from typing import List, Tuple


def campo_obrigatorio(valor, nome: str, erros: List[str]) -> None:
    if valor is None:
        erros.append(f"O campo «{nome}» é obrigatório.")
        return
    if isinstance(valor, str) and not valor.strip():
        erros.append(f"O campo «{nome}» é obrigatório.")


def numero_positivo(valor, nome: str, erros: List[str], zero_ok: bool = False) -> None:
    try:
        n = float(valor)
    except (TypeError, ValueError):
        erros.append(f"O campo «{nome}» deve ser um número válido.")
        return
    if zero_ok:
        if n < 0:
            erros.append(f"O campo «{nome}» não pode ser negativo.")
    else:
        if n <= 0:
            erros.append(f"O campo «{nome}» deve ser maior que zero.")


def validar_cliente(nome: str) -> List[str]:
    erros: List[str] = []
    campo_obrigatorio(nome, "Nome / Razão Social", erros)
    return erros


def validar_dimensionamento(
    cliente_id,
    consumo,
    produtividade,
    modulo,
    tarifa,
) -> List[str]:
    erros: List[str] = []
    if not cliente_id:
        erros.append("Selecione o cliente.")
    numero_positivo(consumo, "Consumo médio (kWh/mês)", erros)
    numero_positivo(produtividade, "Produtividade (kWh/kWp)", erros)
    numero_positivo(modulo, "Potência do módulo (Wp)", erros)
    numero_positivo(tarifa, "Tarifa de energia (R$/kWh)", erros)
    return erros


def validar_empresa(razao_social, nome_fantasia, telefone) -> List[str]:
    erros: List[str] = []
    campo_obrigatorio(razao_social, "Razão Social", erros)
    campo_obrigatorio(nome_fantasia, "Nome Fantasia", erros)
    campo_obrigatorio(telefone, "Telefone", erros)
    return erros


def validar_servico(descricao: str) -> List[str]:
    erros: List[str] = []
    campo_obrigatorio(descricao, "Descrição", erros)
    return erros


def validar_orcamento_publico(nome, telefone, valor_conta) -> List[str]:
    erros: List[str] = []
    campo_obrigatorio(nome, "Nome completo", erros)
    campo_obrigatorio(telefone, "WhatsApp", erros)
    numero_positivo(valor_conta, "Valor da conta de luz", erros)
    return erros


def validar_sistema_solar(potencia_kwp, quantidade_modulos, geracao_mensal) -> List[str]:
    erros: List[str] = []
    numero_positivo(potencia_kwp, "Potência do sistema (kWp)", erros)
    numero_positivo(quantidade_modulos, "Quantidade de módulos", erros)
    numero_positivo(geracao_mensal, "Geração mensal (kWh)", erros, zero_ok=True)
    return erros
