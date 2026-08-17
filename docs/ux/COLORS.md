# Cores — GestorFrete ERP

Tokens HSL (`h s% l%`, sem o wrapper `hsl()` — Tailwind compõe com modificadores de opacidade, ex.
`bg-primary/50`). Definidos em `apps/web/src/styles/globals.css`; nomes wireados no Tailwind via
`packages/config/tailwind.preset.ts`. Ver [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md) para o porquê da
paleta.

## Conteúdo (claro/escuro conforme o tema do usuário)

| Token | Claro | Escuro | Uso |
|---|---|---|---|
| `background` / `foreground` | branco / navy quase-preto | navy escuro / branco | fundo e texto base |
| `card` / `popover` | branco | navy ligeiramente mais claro que `background` | superfícies elevadas |
| `primary` | navy profundo (`222 47% 21%`) | azul mais vivo (`217 91% 60%`) | ações primárias |
| `secondary` / `muted` | cinza-azulado claro | navy escuro | superfícies neutras, texto secundário |
| `accent` / `warning` | âmbar (`38 92% 50%`) | igual | destaque, atenção — mesmo token para os dois |
| `destructive` | vermelho | vermelho mais escuro | ações destrutivas, erro |
| `success` | verde | verde mais claro | confirmação |
| `border` / `input` / `ring` | cinza-azulado claro | navy escuro | bordas, foco |

## Sidebar (`--sidebar-*`) — sempre escura, independente do tema

Não segue `.dark` — é seu próprio conjunto de tokens, deliberadamente fixo em navy escuro nos dois
temas (ver justificativa em `DESIGN_SYSTEM.md`). `--sidebar-primary` reaproveita o âmbar (`accent`)
como cor de destaque do item ativo.

## Branding por tenant

`--tenant-brand` cai no `--primary` até existir um endpoint real de branding (ver
`docs/frontend/README.md`). Nunca usar `--tenant-brand` diretamente em componentes novos sem checar
se ele foi de fato definido — o fallback via `var(--tenant-brand, var(--primary))` já cobre isso no
preset.
