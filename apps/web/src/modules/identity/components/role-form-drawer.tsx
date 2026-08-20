"use client";

import * as React from "react";

import {
  Button,
  Input,
  Label,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  Textarea,
  toast,
} from "@gestorfrete/ui";

import { useCreateRoleMutation } from "@/modules/identity/hooks/use-roles";
import { ApiError } from "@/shared/lib/api-client";

interface RoleFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Create-only, nome/descrição apenas — a matriz de permissões (D216: todo
 * código validado contra `/permissions`) é editada em `/papeis/{id}`, nunca
 * aqui, para não duplicar a lógica de seleção de permissões em dois lugares.
 */
export function RoleFormDrawer({ open, onOpenChange }: RoleFormDrawerProps) {
  const [nome, setNome] = React.useState("");
  const [descricao, setDescricao] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createRole = useCreateRoleMutation();

  function reset() {
    setNome("");
    setDescricao("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createRole.mutateAsync({ nome, descricao: descricao || undefined, permissions: [] });
      toast.success("Papel criado. Configure as permissões na tela de detalhe.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o Papel.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo papel</SheetTitle>
          <SheetDescription>As permissões são configuradas depois, na tela de detalhe do Papel.</SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="role-nome">Nome</Label>
            <Input id="role-nome" required value={nome} onChange={(event) => setNome(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="role-descricao">Descrição</Label>
            <Textarea
              id="role-descricao"
              value={descricao}
              onChange={(event) => setDescricao(event.target.value)}
            />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createRole.isPending}>
              {createRole.isPending ? "Criando…" : "Criar papel"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}
