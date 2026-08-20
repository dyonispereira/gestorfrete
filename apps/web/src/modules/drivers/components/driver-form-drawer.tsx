"use client";

import * as React from "react";

import {
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  toast,
} from "@gestorfrete/ui";
import type { DriverEmploymentType } from "@gestorfrete/types";

import { useCreateDriverMutation } from "@/modules/drivers/hooks/use-drivers";
import { ApiError } from "@/shared/lib/api-client";

const EMPLOYMENT_TYPE_LABEL: Record<DriverEmploymentType, string> = { EMPREGADO: "Empregado", AUTONOMO: "Autônomo" };

interface DriverFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Create-only — CPF and `employment_type` are immutable via PATCH. */
export function DriverFormDrawer({ open, onOpenChange }: DriverFormDrawerProps) {
  const [nome, setNome] = React.useState("");
  const [cpf, setCpf] = React.useState("");
  const [telefone, setTelefone] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [employmentType, setEmploymentType] = React.useState<DriverEmploymentType>("EMPREGADO");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createDriver = useCreateDriverMutation();

  function reset() {
    setNome("");
    setCpf("");
    setTelefone("");
    setEmail("");
    setEmploymentType("EMPREGADO");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createDriver.mutateAsync({
        nome,
        cpf,
        telefone: telefone || undefined,
        email: email || undefined,
        employment_type: employmentType,
      });
      toast.success("Motorista criado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o motorista.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo motorista</SheetTitle>
          <SheetDescription>CPF e vínculo não podem ser alterados depois.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="driver-nome">Nome</Label>
            <Input id="driver-nome" required value={nome} onChange={(event) => setNome(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="driver-cpf">CPF</Label>
            <Input id="driver-cpf" required value={cpf} onChange={(event) => setCpf(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="driver-telefone">Telefone</Label>
            <Input id="driver-telefone" value={telefone} onChange={(event) => setTelefone(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="driver-email">E-mail</Label>
            <Input id="driver-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Vínculo</Label>
            <Select value={employmentType} onValueChange={(value) => setEmploymentType(value as DriverEmploymentType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(EMPLOYMENT_TYPE_LABEL) as DriverEmploymentType[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {EMPLOYMENT_TYPE_LABEL[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createDriver.isPending}>
              {createDriver.isPending ? "Criando…" : "Criar motorista"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}
