"use client";

import * as React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { cn } from "../lib/utils";
import { Button } from "./button";

export interface PaginationProps extends React.HTMLAttributes<HTMLDivElement> {
  page: number;
  limit: number;
  total: number;
  onPageChange: (page: number) => void;
}

/**
 * Prev/next pager for the offset envelope every list endpoint returns
 * (`meta.pagination.{page,limit,total}`) — no numbered page list, matches
 * the "ir para a página 5" use case `PAGINATION.md` describes without
 * inventing a component this Lote doesn't need yet.
 */
const Pagination = React.forwardRef<HTMLDivElement, PaginationProps>(
  ({ className, page, limit, total, onPageChange, ...props }, ref) => {
    const totalPages = Math.max(1, Math.ceil(total / limit));
    const from = total === 0 ? 0 : (page - 1) * limit + 1;
    const to = Math.min(page * limit, total);

    return (
      <div ref={ref} className={cn("flex items-center justify-between gap-4", className)} {...props}>
        <p className="text-sm text-muted-foreground">
          {total === 0 ? "Nenhum resultado" : `${from}–${to} de ${total}`}
        </p>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            Página {page} de {totalPages}
          </span>
          <Button
            type="button"
            variant="outline"
            size="icon"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            aria-label="Página anterior"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            type="button"
            variant="outline"
            size="icon"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            aria-label="Próxima página"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    );
  }
);
Pagination.displayName = "Pagination";

export { Pagination };
