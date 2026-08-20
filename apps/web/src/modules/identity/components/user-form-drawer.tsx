"use client";

import * as React from "react";

import {
  Button,
  Checkbox,
  Input,
  Label,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  toast,
} from "@gestorfrete/ui";

import { useRolesQuery } from "@/modules/identity/hooks/use-roles";
import { useCreateUserMutation } from "@/modules/identity/hooks/use-users";
import { ApiError } from "@/shared/lib/api-client";

interface UserFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Create-only — editing an existing User's data/roles happens on `/usuarios/{id}`. */
export function UserFormDrawer({ open, onOpenChange }: UserFormDrawerProps) {
  const [nome, setNome] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [roleIds, setRoleIds] = React.useState<Set<string>>(new Set());
  const [formError, setFormError] = React.useState<string | null>(null);

  const rolesQuery = useRolesQuery({ limit: 100 });
  const createUser = useCreateUserMutation();

  function reset() {
    setNome("");
    setEmail("");
    setPassword("");
    setRoleIds(new Set());
    setFormError(null);
  }

  function toggleRole(roleId: string) {
    setRoleIds((current) => {
      const next = new Set(current);
      if (next.has(roleId)) next.delete(roleId);
      else next.add(roleId);
      return next;
    });
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createUser.mutateAsync({ nome, email, password, role_ids: Array.from(roleIds) });
      toast.success("Usuário criado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o usuário.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo usuário</SheetTitle>
          <SheetDescription>Crie um acesso e, opcionalmente, atribua Papéis já existentes.</SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="user-nome">Nome</Label>
            <Input id="user-nome" required value={nome} onChange={(event) => setNome(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="user-email">E-mail</Label>
            <Input
              id="user-email"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="user-password">Senha provisória</Label>
            <Input
              id="user-password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Papéis</Label>
            <div className="flex flex-col gap-2 rounded-md border border-border p-3">
              {rolesQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Carregando papéis…</p>
              ) : rolesQuery.data?.data.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nenhum Papel cadastrado ainda.</p>
              ) : (
                rolesQuery.data?.data.map((role) => (
                  <label key={role.id} className="flex items-center gap-2 text-sm">
                    <Checkbox checked={roleIds.has(role.id)} onCheckedChange={() => toggleRole(role.id)} />
                    {role.nome}
                  </label>
                ))
              )}
            </div>
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createUser.isPending}>
              {createUser.isPending ? "Criando…" : "Criar usuário"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}
