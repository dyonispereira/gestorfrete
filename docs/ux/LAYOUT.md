# Grid & Layout — GestorFrete ERP

## Shell (`shared/components/shell/app-shell.tsx`)

```
┌──────────────┬─────────────────────────────────────────┐
│              │  Header (h-header-h = 3.75rem, sticky)   │
│  Sidebar     ├─────────────────────────────────────────┤
│  (fixa,      │                                          │
│  w-sidebar-w │  Conteúdo (max-w-7xl, centralizado,      │
│  = 17rem)    │  padding responsivo px-4→px-8)           │
│              │                                          │
└──────────────┴─────────────────────────────────────────┘
```

`h-dvh` no container raiz (não `h-screen`) — evita o salto de altura de barras de endereço móveis.
Sidebar oculta abaixo de `lg:` (1024px), substituída pelo `MobileSidebar` (Sheet) acionado pelo
botão de menu no Header.

## Responsividade

Mobile-first: toda largura fixa (`w-sidebar-w`, `max-w-7xl`) só se aplica a partir do breakpoint
onde faz sentido; abaixo disso o conteúdo ocupa 100% da viewport. O `Header` esconde o Breadcrumb em
telas pequenas (`hidden lg:block`) para não competir por espaço com o Command/Search e o menu do
usuário — prioridade de informação em telas estreitas.

## Container

`container` do Tailwind (usado pelas páginas via `mx-auto max-w-7xl`) centralizado, `2xl: 1440px` —
teto pensado para tabelas operacionais densas (Viagens, Ordens de Serviço), não para prosa.
