"use client";

import * as React from "react";

interface BreadcrumbLabelContextValue {
  labels: Record<string, string>;
  setLabel: (href: string, label: string | undefined) => void;
}

const BreadcrumbLabelContext = React.createContext<BreadcrumbLabelContextValue | null>(null);

export function BreadcrumbLabelProvider({ children }: { children: React.ReactNode }) {
  const [labels, setLabels] = React.useState<Record<string, string>>({});

  const setLabel = React.useCallback((href: string, label: string | undefined) => {
    setLabels((current) => {
      if (label === undefined) {
        if (!(href in current)) return current;
        const rest = { ...current };
        delete rest[href];
        return rest;
      }
      if (current[href] === label) return current;
      return { ...current, [href]: label };
    });
  }, []);

  const value = React.useMemo(() => ({ labels, setLabel }), [labels, setLabel]);

  return <BreadcrumbLabelContext.Provider value={value}>{children}</BreadcrumbLabelContext.Provider>;
}

function useBreadcrumbLabelContext(): BreadcrumbLabelContextValue {
  const context = React.useContext(BreadcrumbLabelContext);
  if (!context) throw new Error("useBreadcrumbLabelContext must be used within a BreadcrumbLabelProvider");
  return context;
}

/** Read side, used by `BreadcrumbNav` — a map of `href` → dynamic label. */
export function useBreadcrumbLabels(): Record<string, string> {
  return useBreadcrumbLabelContext().labels;
}

/**
 * Write side — a detail page calls this once its entity loads (e.g. a
 * User's `nome`) so `/usuarios/{id}` shows a name instead of a raw UUID in
 * the breadcrumb. Clears itself on unmount so a stale label never leaks
 * into the next page that happens to reuse the same `href`.
 */
export function useBreadcrumbLabel(href: string, label: string | undefined): void {
  const { setLabel } = useBreadcrumbLabelContext();

  React.useEffect(() => {
    setLabel(href, label);
    return () => setLabel(href, undefined);
  }, [href, label, setLabel]);
}
