"use client";

import * as React from "react";

import { Button, Input, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, toast } from "@gestorfrete/ui";

import { useCreateEmployeeMutation } from "@/modules/identity/hooks/use-employees";
import { ApiError } from "@/shared/lib/api-client";

interface EmployeeFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** No phone/email/CPF fields — `EmployeeResponse` really only has nome/cargo/hired_at/status. */
export function EmployeeFormDrawer({ open, onOpenChange }: EmployeeFormDrawerProps) {
  const [nome, setNome] = React.useState("");
  const [cargo, setCargo] = React.useState("");
  const [hiredAt, setHiredAt] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createEmployee = useCreateEmployeeMutation();

  function reset() {
    setNome("");
    setCargo("");
    setHiredAt("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createEmployee.mutateAsync({ nome, cargo, hired_at: hiredAt || undefined });
      toast.success("Funcionário criado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o funcionário.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo funcionário</SheetTitle>
          <SheetDescription>Vincular a um Usuário é feito na tela de Usuários, não aqui.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="employee-nome">Nome</Label>
            <Input id="employee-nome" required value={nome} onChange={(event) => setNome(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="employee-cargo">Cargo</Label>
            <Input id="employee-cargo" required value={cargo} onChange={(event) => setCargo(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="employee-hired-at">Data de admissão</Label>
            <Input id="employee-hired-at" type="date" value={hiredAt} onChange={(event) => setHiredAt(event.target.value)} />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createEmployee.isPending}>
              {createEmployee.isPending ? "Criando…" : "Criar funcionário"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}
