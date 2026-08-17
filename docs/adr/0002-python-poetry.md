# ADR 0002: Poetry para gerenciamento de dependências Python

## Status
Aceito

## Contexto
O backend precisa de um gerenciador de dependências e ambientes virtuais maduro, com lockfile
determinístico, adequado a um projeto enterprise de longo prazo com múltiplos bounded contexts e
dependências de infraestrutura (SQLAlchemy, Alembic, aio-pika, MinIO SDK, etc.).

## Decisão
Usar **Poetry** com `package-mode = false` (o backend é uma aplicação, não uma biblioteca
distribuível — não há necessidade de empacotar/publicar `gestorfrete-api`).

## Alternativas consideradas
- **uv**: ferramenta mais nova e mais rápida (Rust), compatível com `pyproject.toml`, mas com
  adoção enterprise ainda menos consolidada no momento desta decisão.
- **pip + requirements.txt**: universal, porém sem lockfile robusto nativo e sem gerenciamento de
  ambientes — mais frágil para um projeto que vai crescer por muitos módulos e desenvolvedores ao
  longo de meses.

## Consequências
- `apps/api/pyproject.toml` declara as dependências de produção e de desenvolvimento
  (`tool.poetry.group.dev.dependencies`: pytest, ruff, mypy).
- `poetry install` cria o ambiente virtual local; `poetry.lock` (gerado no primeiro `poetry install`
  real) garante reprodutibilidade entre desenvolvedores e ambientes de CI/CD.
- O layout do código-fonte usa `src/` como raiz (fora de um pacote Python nomeado), com
  `pythonpath = ["src"]` configurado em `[tool.pytest.ini_options]` e execução via
  `uvicorn main:app --app-dir src`.
