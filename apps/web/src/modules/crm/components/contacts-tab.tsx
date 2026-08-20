"use client";

import * as React from "react";
import { Plus, UserRound } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
  Button,
  Input,
  Label,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  toast,
} from "@gestorfrete/ui";
import type { Contact, CreateContactRequest } from "@gestorfrete/types";

import {
  useClientContactsQuery,
  useCreateClientContactMutation,
  useDeleteClientContactMutation,
  useUpdateClientContactMutation,
} from "@/modules/crm/hooks/use-contacts";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const EMPTY_FORM: CreateContactRequest = { nome: "", cargo: "", telefone: "", email: "" };

interface ContactsTabProps {
  clientId: string;
  editable: boolean;
}

/** Exclusive to Cliente — `crm.client_contact.*`, not polymorphic like Endereço. */
export function ContactsTab({ clientId, editable }: ContactsTabProps) {
  const contactsQuery = useClientContactsQuery(clientId);
  const createContact = useCreateClientContactMutation(clientId);
  const updateContact = useUpdateClientContactMutation(clientId);
  const deleteContact = useDeleteClientContactMutation(clientId);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Contact | null>(null);
  const [form, setForm] = React.useState<CreateContactRequest>(EMPTY_FORM);
  const [formError, setFormError] = React.useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setDrawerOpen(true);
  }

  function openEdit(contact: Contact) {
    setEditing(contact);
    setForm({
      nome: contact.nome,
      cargo: contact.cargo ?? "",
      telefone: contact.telefone ?? "",
      email: contact.email ?? "",
    });
    setFormError(null);
    setDrawerOpen(true);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    const body: CreateContactRequest = {
      nome: form.nome,
      cargo: form.cargo || undefined,
      telefone: form.telefone || undefined,
      email: form.email || undefined,
    };
    try {
      if (editing) {
        await updateContact.mutateAsync({ contactId: editing.id, body });
        toast.success("Contato atualizado.");
      } else {
        await createContact.mutateAsync(body);
        toast.success("Contato adicionado.");
      }
      setDrawerOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível salvar o contato.");
    }
  }

  async function handleDelete(contactId: string) {
    try {
      await deleteContact.mutateAsync(contactId);
      toast.success("Contato removido.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível remover o contato.");
    }
  }

  if (contactsQuery.isLoading) return <LoadingState rows={3} />;
  if (contactsQuery.error)
    return <ErrorState description="Não foi possível carregar os contatos." onRetry={() => contactsQuery.refetch()} />;

  const contacts = contactsQuery.data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      {editable ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Novo contato
          </Button>
        </div>
      ) : null}

      {contacts.length === 0 ? (
        <EmptyState icon={UserRound} title="Nenhum contato cadastrado" />
      ) : (
        <div className="flex flex-col gap-3">
          {contacts.map((contact) => (
            <div key={contact.id} className="flex items-start justify-between gap-4 rounded-md border border-border p-4">
              <div className="flex flex-col gap-0.5">
                <p className="text-sm font-medium text-foreground">{contact.nome}</p>
                {contact.cargo ? <p className="text-sm text-muted-foreground">{contact.cargo}</p> : null}
                <p className="text-sm text-muted-foreground">{[contact.telefone, contact.email].filter(Boolean).join(" — ") || "—"}</p>
              </div>
              {editable ? (
                <div className="flex shrink-0 gap-2">
                  <Button size="sm" variant="outline" onClick={() => openEdit(contact)}>
                    Editar
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button size="sm" variant="destructive">
                        Remover
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Remover {contact.nome}?</AlertDialogTitle>
                        <AlertDialogDescription>Essa ação não pode ser desfeita pela tela.</AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancelar</AlertDialogCancel>
                        <AlertDialogAction onClick={() => handleDelete(contact.id)}>Remover</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent className="flex flex-col gap-6 sm:max-w-md">
          <SheetHeader>
            <SheetTitle>{editing ? "Editar contato" : "Novo contato"}</SheetTitle>
            <SheetDescription>Pessoa de contato deste cliente.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="contact-nome">Nome</Label>
              <Input id="contact-nome" required value={form.nome} onChange={(event) => setForm((f) => ({ ...f, nome: event.target.value }))} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="contact-cargo">Cargo</Label>
              <Input id="contact-cargo" value={form.cargo} onChange={(event) => setForm((f) => ({ ...f, cargo: event.target.value }))} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="contact-telefone">Telefone</Label>
              <Input id="contact-telefone" value={form.telefone} onChange={(event) => setForm((f) => ({ ...f, telefone: event.target.value }))} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="contact-email">E-mail</Label>
              <Input id="contact-email" type="email" value={form.email} onChange={(event) => setForm((f) => ({ ...f, email: event.target.value }))} />
            </div>

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDrawerOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createContact.isPending || updateContact.isPending}>
                {createContact.isPending || updateContact.isPending ? "Salvando…" : "Salvar"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}
