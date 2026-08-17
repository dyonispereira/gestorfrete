# Componentes — GestorFrete ERP

Biblioteca compartilhada em `packages/ui/` (`@gestorfrete/ui`), padrão shadcn/ui: Radix UI
primitives (acessibilidade/comportamento) + Tailwind (estilo) + `class-variance-authority`
(variantes tipadas) + `tailwind-merge` (composição de className sem conflito). Escritos à mão nesta
Sprint 12 Lote 1, não gerados pela CLI interativa do shadcn — o monorepo já define onde cada
componente mora (`packages/ui`) e como é consumido (`@gestorfrete/ui`), então gerar direto ali é
mais direto que rodar a CLI e mover arquivos depois.

## Inventário (Lote 1)

Button, Input, Label, Card (+ Header/Title/Description/Content/Footer), Avatar, Badge, Separator,
Skeleton, ScrollArea, Tooltip, Dialog, DropdownMenu, Sheet, Command (cmdk), Breadcrumb.

## Regra: todo componente que usa Radix precisa de `"use client"`

Radix cria contexto React (`createContext`) na avaliação do próprio módulo, não só quando
renderizado — importar um componente Radix a partir de um Server Component (Next.js App Router)
sem o boundary `"use client"` quebra com `createContext is not a function`. Todo arquivo em
`packages/ui/src/components/` tem `"use client"` na primeira linha por isso, mesmo os que não
usariam hooks sozinhos (Button, Card) — consistência do pacote inteiro importa mais que a economia
marginal de não marcar os poucos que tecnicamente poderiam ficar sem.

## Como este inventário cresce

Um componente entra aqui quando um lote de negócio genuinamente precisa dele (Table/DataGrid para
Cadastros, Select/Combobox para formulários, etc.) — nunca especulativamente adiantado.
