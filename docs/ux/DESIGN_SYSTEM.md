# Design System — GestorFrete ERP

Fundação visual construída na Sprint 12 Lote 1 (Frontend). Ver
[`../frontend/README.md`](../frontend/README.md) para o que foi implementado e como foi verificado;
este documento registra o *porquê* das escolhas, não repete a lista de arquivos.

## Princípio norteador

O usuário pediu explicitamente que o GestorFrete "pareça um ERP moderno e premium, não um SaaS
genérico". Duas decisões de design carregam esse objetivo:

1. **Paleta navy + âmbar**, não o azul/roxo-gradiente default de template SaaS.
2. **Barra lateral sempre escura**, independente do tema claro/escuro do conteúdo — uma âncora
   visual fixa, como a maioria dos ERPs de operação (WMS/TMS) usa, em vez de tudo claro.

Ver [`COLORS.md`](./COLORS.md) para os tokens exatos.

## Onde os tokens vivem

- `packages/config/tailwind.preset.ts` — nomes dos tokens no Tailwind (`bg-primary`,
  `text-sidebar-foreground`, etc.), compartilhado por todo app do monorepo via `presets`.
- `apps/web/src/styles/globals.css` — valores reais dos tokens (HSL, `:root` + `.dark`).

Novo app do monorepo (se algum dia existir) herda a paleta automaticamente ao estender o preset —
nunca duplicando os valores HSL.

## Tema por tenant

`core/tenant/branding.ts` já injeta `--tenant-brand` no `<html>` em runtime — a Shell está pronta
para branding por tenant, mas a API não tem `GET/PATCH /tenant/settings/branding` ainda
(`docs/api/002-tenants.md` adia isso explicitamente). Hoje `--tenant-brand` sempre cai no
`--primary` padrão. Ver a nota completa em `docs/frontend/README.md` (seção "Fundação de
Auth/Tenant/RBAC").
