export function formatMoney(value: string | number): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function formatPercent(value: string | null): string {
  if (value === null) return "—";
  return `${Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
}

export function formatKm(value: string | null): string {
  if (value === null) return "Indisponível";
  return `${Number(value).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} km`;
}

export function formatMoneyPerKm(value: string | null): string {
  if (value === null) return "Indisponível";
  return `${formatMoney(value)}/km`;
}
