# Modules

Organização *feature-sliced* do front-end: cada pasta espelha um bounded context do backend
(`apps/api/src/modules`), mantendo a mesma linguagem ubíqua dos dois lados da stack. Isso evita que
o front-end vire uma pasta única de "components" desorganizada conforme o ERP cresce para dezenas
de telas por domínio.

Cada módulo é internamente organizado em `components/`, `hooks/`, `services/` e `types/` — veja o
`README.md` de cada módulo para a responsabilidade de negócio específica.
