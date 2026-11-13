# Extrator de notas fiscais com agente de IA

API em FastAPI que recebe uma nota fiscal ou fatura (imagem ou texto), extrai CNPJ do emitente, valor total e data de emissão com um agente que usa **tool calling**, valida o resultado e grava em PostgreSQL.

Todos os documentos de exemplo são fictícios.

## Problema

Lançar nota fiscal à mão é lento e erra: alguém abre o PDF, procura o CNPJ, copia o total e digita a data no sistema. Um modelo de linguagem sozinho também erra (inventa dígito, troca vírgula por ponto). Aqui o modelo decide **o que** procurar, mas quem lê o documento são funções determinísticas e testadas, e nada vai para o banco sem passar pela validação.

## Como funciona

```
arquivo ──► OCR (Tesseract, pt-BR) ──► texto
                                         │
                         ┌───────────────▼───────────────┐
                         │ agente (laço de tool calling) │
                         │  modelo pede ferramenta  ◄──┐ │
                         │  código executa ─────────────┘ │
                         └───────────────┬───────────────┘
                                         ▼
                     validação (Pydantic: CNPJ com 14 dígitos, valor ≥ 0, data real)
                                         ▼
                                 PostgreSQL (SQLAlchemy)
```

- **Ferramentas** (`app/ferramentas.py`): `extrair_cnpj` (confere os dígitos verificadores), `extrair_valor_total` (prioriza a linha de total), `extrair_data_emissao` (DD/MM/AAAA ou ISO).
- **Agente** (`app/agente.py`): laço com limite de passos, lista branca de ferramentas e validação da resposta final. Se o modelo pedir uma ferramenta fora da lista, entrar em loop ou devolver dado inválido, a requisição falha com 422 e nada é gravado.
- **Cérebro trocável** (`app/llm.py`):
  - `RoteiroLocal`: sem rede e sem custo, usado nos testes e no CI.
  - `ClienteCompativelOpenAI`: qualquer endpoint `/chat/completions` com tools (DeepSeek, OpenAI etc.), ligado por variáveis de ambiente.

## Stack

Python 3.12 · FastAPI · Pydantic · SQLAlchemy 2 · PostgreSQL 16 · Tesseract OCR · Docker / Docker Compose · pytest · Ruff · GitHub Actions

## Como rodar

Com Docker:

```bash
cp .env.example .env          # opcional: preencha LLM_* para usar um modelo real
docker compose up --build
curl -F arquivo=@exemplos/nota-ficticia-01.txt localhost:8000/notas
```

Documentação interativa em `http://localhost:8000/docs`.

Sem Docker (usa SQLite local):

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Testes

```bash
pytest -q        # 14 testes: ferramentas, guardas do agente e fluxo da API
ruff check .
```

O CI (`.github/workflows/ci.yml`) roda lint, testes e o build da imagem Docker a cada push.

## Endpoints

| Método | Rota | O que faz |
|---|---|---|
| `POST` | `/notas` | Envia o arquivo (`.txt`, `.png`, `.jpg`, `.tif`) e devolve os dados extraídos |
| `GET` | `/notas?cnpj=` | Lista as últimas 100 notas, com filtro opcional por CNPJ |
| `GET` | `/notas/{id}` | Uma nota |
| `GET` | `/saude` | Health check |

## Limites

- É uma demo: extrai três campos. Itens, impostos e XML da NF-e ficam para uma próxima versão.
- PDF ainda não é aceito direto. Converta para imagem antes.
- O OCR depende da qualidade da imagem. Foto torta ou com pouca luz reduz o acerto.
