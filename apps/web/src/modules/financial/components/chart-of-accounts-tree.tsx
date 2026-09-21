"use client";

import { Badge } from "@gestorfrete/ui";
import type { ChartOfAccounts, ChartOfAccountsStatus, ChartOfAccountsType } from "@gestorfrete/types";

const TYPE_LABEL: Record<ChartOfAccountsType, string> = { RECEITA: "Receita", DESPESA: "Despesa" };
const TYPE_VARIANT: Record<ChartOfAccountsType, "success" | "secondary"> = { RECEITA: "success", DESPESA: "secondary" };
const STATUS_VARIANT: Record<ChartOfAccountsStatus, "outline" | "destructive"> = { ATIVO: "outline", INATIVO: "destructive" };

interface Node {
  account: ChartOfAccounts;
  children: Node[];
}

function buildTree(accounts: ChartOfAccounts[]): Node[] {
  const byId = new Map(accounts.map((account) => [account.id, { account, children: [] as Node[] }]));
  const roots: Node[] = [];
  for (const node of byId.values()) {
    if (node.account.parent_id && byId.has(node.account.parent_id)) {
      byId.get(node.account.parent_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  }
  return roots;
}

function TreeRow({ node, depth, onSelect }: { node: Node; depth: number; onSelect: (account: ChartOfAccounts) => void }) {
  return (
    <>
      <button
        type="button"
        onClick={() => onSelect(node.account)}
        className="flex w-full items-center gap-2 rounded-md py-1.5 pr-2 text-left text-sm hover:bg-muted"
        style={{ paddingLeft: `${depth * 1.5 + 0.5}rem` }}
      >
        {depth > 0 ? <span className="text-muted-foreground">└</span> : null}
        <span className="font-mono text-xs text-muted-foreground">{node.account.account_code}</span>
        <span className="font-medium">{node.account.name}</span>
        <Badge variant={TYPE_VARIANT[node.account.type]}>{TYPE_LABEL[node.account.type]}</Badge>
        {node.account.status === "INATIVO" ? <Badge variant={STATUS_VARIANT.INATIVO}>Inativo</Badge> : null}
      </button>
      {node.children.map((child) => (
        <TreeRow key={child.account.id} node={child} depth={depth + 1} onSelect={onSelect} />
      ))}
    </>
  );
}

/** Árvore real, não tabela plana disfarçada — `parent_id` já existe no contrato (D184), a
 * hierarquia é montada aqui a partir da lista completa retornada por `GET /plano-contas`. */
export function ChartOfAccountsTree({ accounts, onSelect }: { accounts: ChartOfAccounts[]; onSelect: (account: ChartOfAccounts) => void }) {
  const tree = buildTree(accounts);
  return (
    <div className="flex flex-col gap-0.5 rounded-md border border-border p-2">
      {tree.map((node) => (
        <TreeRow key={node.account.id} node={node} depth={0} onSelect={onSelect} />
      ))}
    </div>
  );
}
