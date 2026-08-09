# GMTECH Manager

Sistema ERP / CRM para integradores de energia solar — GMTECH Soluções Elétricas.

## Fluxo principal

1. **Cliente** cadastrado (ou lead convertido)
2. **Dimensionador** calcula o sistema (Lei 14.300 / Fio B)
3. **Proposta** gerada a partir do dimensionamento (já precificada com preço/kWp da empresa)
4. Envie o **link de assinatura digital** ao cliente (ou marque Aceita manualmente)
5. Ao aceitar/assinar → **Ordem de Serviço** criada automaticamente
6. Acompanhe a obra (lista ou **Kanban**) até **Concluído**

### Precificação
Em **Empresa** configure o **Preço por kWp**. Ao gerar proposta pelo dimensionador, o valor é calculado automaticamente (potência × preço/kWp). Você pode ajustar depois nos itens.

### Assinatura digital
Na proposta, use **Link de assinatura digital**. O cliente abre o link, informa nome/CPF e aceita. A proposta vira Aceita e a OS é criada automaticamente, com registro de data e IP.

## Módulos

- Dashboard (pipeline)
- Clientes
- Leads (simulador público `/orcamento`)
- Dimensionador / Dimensionamentos
- Propostas (PDF, WhatsApp, status, assinatura digital)
- Ordens de Serviço (lista + Kanban)
- Catálogo de serviços/produtos
- Dados da empresa + parâmetros do simulador + preço/kWp

## Como rodar

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse `http://127.0.0.1:8000`

Login padrão: `admin@gmtech.local` / `admin123`

## Observações

- O banco SQLite fica em `app/gmtech.db` (não versionar em produção).
- Logo: `app/static/img/logo.svg` / `logo.PNG`
- Destinado a ser oferecido como plataforma para integradores (cada um com sua operação).
