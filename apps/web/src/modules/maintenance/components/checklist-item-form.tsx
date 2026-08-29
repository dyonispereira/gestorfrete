"use client";

import * as React from "react";
import { Plus, Trash2 } from "lucide-react";

import { Button, Checkbox, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { ChecklistItem } from "@gestorfrete/types";

interface ChecklistItemFormProps {
  items: ChecklistItem[];
  onChange: (items: ChecklistItem[]) => void;
}

/** Editor inline dos itens — sem Modelo de Checklist configurável nesta fundação (ver domain doc):
 * cada item é digitado na hora, marcado crítico ou não, e respondido Sim/Não. */
export function ChecklistItemForm({ items, onChange }: ChecklistItemFormProps) {
  function addItem() {
    onChange([...items, { descricao: "", critico: false, resposta: undefined }]);
  }

  function removeItem(index: number) {
    onChange(items.filter((_, i) => i !== index));
  }

  function updateItem(index: number, patch: Partial<ChecklistItem>) {
    onChange(items.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  return (
    <div className="flex flex-col gap-3">
      {items.map((item, index) => (
        <div key={index} className="flex flex-col gap-2 rounded-md border border-border p-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <Label htmlFor={`checklist-item-${index}`}>Item</Label>
            <Input
              id={`checklist-item-${index}`}
              required
              value={item.descricao}
              onChange={(event) => updateItem(index, { descricao: event.target.value })}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <Checkbox checked={item.critico} onCheckedChange={(checked) => updateItem(index, { critico: checked === true })} />
            Crítico
          </label>
          <div className="sm:w-40">
            <Label htmlFor={`checklist-item-resposta-${index}`}>Resposta</Label>
            <Select
              value={item.resposta === undefined ? "" : item.resposta ? "sim" : "nao"}
              onValueChange={(value) => updateItem(index, { resposta: value === "sim" })}
            >
              <SelectTrigger id={`checklist-item-resposta-${index}`}>
                <SelectValue placeholder="Selecione" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sim">Conforme</SelectItem>
                <SelectItem value="nao">Não conforme</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={() => removeItem(index)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ))}
      <Button type="button" variant="outline" size="sm" className="self-start" onClick={addItem}>
        <Plus className="h-4 w-4" />
        Adicionar item
      </Button>
    </div>
  );
}
