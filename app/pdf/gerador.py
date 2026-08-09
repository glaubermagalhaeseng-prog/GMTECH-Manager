from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

from app.pdf.paginas import (
    pagina_capa,
    pagina_como_funciona,
    pagina_projeto,
    pagina_investimento_economia,
    pagina_retorno,
    pagina_processo,
    pagina_sobre_contato,
    desenhar_capa_canva,
    rodape_e_marca_dagua,
)
from app.pdf.tabela import desenhar_tabela
from app.pdf.estilos import titulo_dois_tons, secao_titulo


def gerar_pdf_proposta(caminho, proposta, itens, empresa, sistema=None, link_assinatura=None):
    """
    PDF comercial com capa no estilo Canva (fundo + dados dinâmicos).
    """

    # ------------------------------------------------------------
    # Economia mensal "oficial": sempre que a conta atual e a conta
    # residual estiverem preenchidas, a economia real é a diferença
    # entre elas — não o campo digitado à parte no cadastro do
    # sistema, que pode ter sido preenchido com outro valor e ficar
    # inconsistente com a tabela "Sua Economia". Corrigindo aqui
    # centraliza o número certo em toda a proposta (payback,
    # gráfico de retorno e capa incluídos).
    # ------------------------------------------------------------
    if sistema:
        sistema = dict(sistema)
        valor_atual = sistema.get("valor_conta_atual") or 0
        valor_residual = sistema.get("valor_conta_residual")
        if valor_atual and valor_residual is not None:
            sistema["economia_mensal"] = max(0, valor_atual - valor_residual)

    documento = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        topMargin=48,
        bottomMargin=40,
        leftMargin=45,
        rightMargin=45,
    )

    # Contexto da capa para o canvas
    documento._capa_ctx = {
        "proposta": proposta,
        "sistema": sistema,
        "empresa": empresa,
    }

    # Contexto do rodapé/marca d'água (páginas 2+)
    documento._rodape_cliente = (proposta or {}).get("cliente_nome", "")
    numero_id = (proposta or {}).get("id")
    documento._rodape_numero = f"PROP-{numero_id:04d}" if numero_id else ""
    documento._rodape_rascunho = ((proposta or {}).get("status") == "Rascunho")

    elementos = []

    pagina_capa(elementos, proposta, sistema, empresa)
    pagina_como_funciona(elementos)
    pagina_projeto(elementos, sistema, proposta)
    pagina_investimento_economia(elementos, proposta, sistema)
    pagina_retorno(elementos, proposta, sistema)
    pagina_processo(elementos)

    # Itens da proposta em página própria
    elementos.append(PageBreak())
    elementos.append(
        Paragraph(titulo_dois_tons("ITENS DA", "PROPOSTA"), secao_titulo)
    )
    elementos.append(Spacer(1, 12))
    desenhar_tabela(elementos, itens)
    elementos.append(Spacer(1, 18))

    pagina_sobre_contato(elementos, empresa, link_assinatura)

    documento.build(
        elementos,
        onFirstPage=desenhar_capa_canva,
        onLaterPages=rodape_e_marca_dagua,
    )
