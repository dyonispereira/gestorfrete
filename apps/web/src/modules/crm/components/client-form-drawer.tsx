"use client";

import * as React from "react";

import { Button, Input, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, toast } from "@gestorfrete/ui";

import { useCreateClientMutation } from "@/modules/crm/hooks/use-clients";
import { ApiError } from "@/shared/lib/api-client";

interface ClientFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Create-only — `document` (CNPJ/CPF) is immutable, there's no rename-document endpoint. */
export function ClientFormDrawer({ open, onOpenChange }: ClientFormDrawerProps) {
  const [razaoSocial, setRazaoSocial] = React.useState("");
  const [nomeFantasia, setNomeFantasia] = React.useState("");
  const [document, setDocumentValue] = React.useState("");
  const [telefone, setTelefone] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createClient = useCreateClientMutation();

  function reset() {
    setRazaoSocial("");
    setNomeFantasia("");
    setDocumentValue("");
    setTelefone("");
    setEmail("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createClient.mutateAsync({
        razao_social: razaoSocial,
        nome_fantasia: nomeFantasia || undefined,
        document,
        telefone: telefone || undefined,
        email: email || undefined,
      });
      toast.success("Cliente criado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o cliente.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo cliente</SheetTitle>
          <SheetDescription>O documento (CNPJ/CPF) não pode ser alterado depois.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="client-razao-social">Razão social</Label>
            <Input id="client-razao-social" required value={razaoSocial} onChange={(event) => setRazaoSocial(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="client-nome-fantasia">Nome fantasia</Label>
            <Input id="client-nome-fantasia" value={nomeFantasia} onChange={(event) => setNomeFantasia(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="client-document">CNPJ/CPF</Label>
            <Input id="client-document" required value={document} onChange={(event) => setDocumentValue(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="client-telefone">Telefone</Label>
            <Input id="client-telefone" value={telefone} onChange={(event) => setTelefone(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="client-email">E-mail</Label>
            <Input id="client-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createClient.isPending}>
              {createClient.isPending ? "Criando…" : "Criar cliente"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}
