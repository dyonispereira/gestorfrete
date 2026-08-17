# Tipografia — GestorFrete ERP

Fonte: **Inter** (via `next/font/google`, `apps/web/src/app/layout.tsx`), exposta como
`--font-sans`; **JetBrains Mono** como `--font-mono` para dado técnico (IDs, códigos, JSON). Ambas
carregadas com `display: swap` — sem flash de fonte não estilizada bloqueando o layout.

## Escala (`packages/config/tailwind.preset.ts`)

Escala levemente mais compacta que o padrão Tailwind — um ERP de densidade operacional mostra mais
dado por tela que um site de marketing:

| Classe | Tamanho | Uso |
|---|---|---|
| `text-xs` | 12px | metadados, badges, timestamps |
| `text-sm` | 13px | corpo padrão de UI (labels, itens de menu, tabelas) |
| `text-base` | 14px | corpo de conteúdo (o `body` usa este, não 16px) |
| `text-lg`–`text-4xl` | 16–36px | títulos, hierarquia de página |

Peso: `font-medium` para labels/itens interativos, `font-semibold` para títulos — nunca `font-bold`
sozinho como única forma de hierarquia (par sempre com tamanho).
