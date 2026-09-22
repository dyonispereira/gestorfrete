"use client";

import { Input, Label } from "@gestorfrete/ui";

export interface Period {
  dateFrom: string;
  dateTo: string;
}

export function PeriodFilter({ period, onChange }: { period: Period; onChange: (period: Period) => void }) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="management-result-period-from">Período — de</Label>
        <Input
          id="management-result-period-from"
          type="date"
          value={period.dateFrom}
          onChange={(event) => onChange({ ...period, dateFrom: event.target.value })}
          className="w-40"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="management-result-period-to">até</Label>
        <Input
          id="management-result-period-to"
          type="date"
          value={period.dateTo}
          onChange={(event) => onChange({ ...period, dateTo: event.target.value })}
          className="w-40"
        />
      </div>
    </div>
  );
}
