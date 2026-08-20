"use client";

import { Fragment } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@gestorfrete/ui";

import { NAV_GROUPS } from "@/core/rbac/nav-config";
import { useBreadcrumbLabels } from "./breadcrumb-label-context";

const ALL_ITEMS = NAV_GROUPS.flatMap((group) => group.items);

function labelFor(href: string): string {
  return ALL_ITEMS.find((item) => item.href === href)?.label ?? href;
}

/**
 * Derived from the current route + `nav-config` labels — never a
 * hand-maintained per-page title. A dynamic segment (`/usuarios/{id}`) has
 * no `nav-config` entry to match, so it falls back to the raw href unless
 * the page itself registered a friendlier label via `useBreadcrumbLabel`
 * (e.g. the User's `nome`, once loaded).
 */
export function BreadcrumbNav() {
  const pathname = usePathname() ?? "/dashboard";
  const dynamicLabels = useBreadcrumbLabels();
  const segments = pathname.split("/").filter(Boolean);

  const crumbs = segments.map((_, index) => {
    const href = `/${segments.slice(0, index + 1).join("/")}`;
    return { href, label: dynamicLabels[href] ?? labelFor(href) };
  });

  if (crumbs.length === 0) return null;

  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <Link href="/dashboard">GestorFrete</Link>
          </BreadcrumbLink>
        </BreadcrumbItem>
        {crumbs.map((crumb, index) => (
          <Fragment key={crumb.href}>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              {index === crumbs.length - 1 ? (
                <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
              ) : (
                <BreadcrumbLink asChild>
                  <Link href={crumb.href}>{crumb.label}</Link>
                </BreadcrumbLink>
              )}
            </BreadcrumbItem>
          </Fragment>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
