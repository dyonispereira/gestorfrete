import type { LucideIcon } from "lucide-react";
import {
  Banknote,
  Bot,
  Building2,
  ClipboardList,
  Container,
  FileStack,
  Gauge,
  LayoutDashboard,
  LineChart,
  ShieldCheck,
  Truck,
  UserCog,
  Users,
  Wrench,
} from "lucide-react";

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon: LucideIcon;
  /** RBAC codes gating this item — OR semantics (any one held is enough). */
  requiredPermissions: string[];
  /** `true` once a real page exists at `href`; otherwise routes to the module placeholder. */
  implemented?: boolean;
  description: string;
}

export interface NavGroup {
  id: string;
  label: string;
  items: NavItem[];
}

/**
 * The full universe of possible navigation entries, mirroring
 * `RBAC_MATRIX.md` §7.1–§7.29's real module/resource taxonomy — not invented
 * here. This list is static (there are only so many bounded contexts), but
 * what actually renders in the Sidebar is computed at runtime from the
 * User's resolved permissions (`PermissionsProvider`) — see
 * `useAuthorizedNav`. `implemented` flips on, module by module, as each
 * lote lands; until then the item is real and permission-gated, it just
 * opens the shared "módulo ainda não implementado" placeholder instead of a
 * business screen. Identity (`usuarios`/`papeis`/`permissoes`) landed first
 * — deliberately, to validate the Shell (tables/forms/drawers/RBAC) against
 * real data before any other lote reuses the same pattern; every other item
 * below is still a placeholder.
 */
export const NAV_GROUPS: NavGroup[] = [
  {
    id: "overview",
    label: "Visão Geral",
    items: [
      {
        id: "dashboard",
        label: "Painel",
        href: "/dashboard",
        icon: LayoutDashboard,
        requiredPermissions: [],
        implemented: true,
        description: "Resumo operacional do tenant.",
      },
    ],
  },
  {
    id: "cadastros",
    label: "Cadastros",
    items: [
      {
        id: "clients",
        label: "Clientes",
        href: "/clientes",
        icon: Users,
        requiredPermissions: ["crm.client.view"],
        implemented: true,
        description: "Clientes da transportadora.",
      },
      {
        id: "suppliers",
        label: "Fornecedores",
        href: "/fornecedores",
        icon: Building2,
        requiredPermissions: ["maintenance.supplier.view"],
        implemented: true,
        description: "Fornecedores cadastrados.",
      },
      {
        id: "drivers",
        label: "Motoristas",
        href: "/motoristas",
        icon: Users,
        requiredPermissions: ["drivers.driver.view"],
        implemented: true,
        description: "Motoristas da frota.",
      },
      {
        id: "employees",
        label: "Funcionários",
        href: "/funcionarios",
        icon: UserCog,
        requiredPermissions: ["identity_access.employee.view"],
        implemented: true,
        description: "Funcionários da transportadora.",
      },
      {
        id: "cost-centers",
        label: "Centros de Custo",
        href: "/centros-custo",
        icon: Banknote,
        requiredPermissions: ["financial.cost_center.view"],
        implemented: true,
        description: "Centros de custo do tenant.",
      },
    ],
  },
  {
    id: "fleet",
    label: "Frota",
    items: [
      {
        id: "vehicles",
        label: "Veículos",
        href: "/veiculos",
        icon: Truck,
        requiredPermissions: ["fleet.vehicle.view"],
        implemented: true,
        description: "Veículos tracionadores da frota.",
      },
      {
        id: "implements",
        label: "Implementos",
        href: "/implementos",
        icon: Container,
        requiredPermissions: ["fleet.implement.view"],
        implemented: true,
        description: "Carretas e outros implementos da frota.",
      },
      {
        id: "availability",
        label: "Disponibilidade",
        href: "/disponibilidade",
        icon: Gauge,
        requiredPermissions: ["fleet.vehicle.view_availability"],
        implemented: true,
        description: "Consulta somente leitura da disponibilidade da frota.",
      },
    ],
  },
  {
    id: "operacao",
    label: "Operação",
    items: [
      {
        id: "trips",
        label: "Viagens",
        href: "/viagens",
        icon: ClipboardList,
        requiredPermissions: ["freight.trip.view"],
        description: "Viagens e entregas.",
        implemented: true,
      },
    ],
  },
  {
    id: "maintenance",
    label: "Manutenção",
    items: [
      {
        id: "work-orders",
        label: "Ordens de Serviço",
        href: "/m/work-orders",
        icon: Wrench,
        requiredPermissions: ["maintenance.work_order.view"],
        description: "Ordens de serviço de manutenção.",
      },
    ],
  },
  {
    id: "financial",
    label: "Financeiro",
    items: [
      {
        id: "invoices",
        label: "Faturas",
        href: "/m/invoices",
        icon: Banknote,
        requiredPermissions: ["financial.invoice.view"],
        description: "Faturas e contas do tenant.",
      },
    ],
  },
  {
    id: "fiscal",
    label: "Fiscal",
    items: [
      {
        id: "ctes",
        label: "CT-e / MDF-e",
        href: "/m/fiscal",
        icon: FileStack,
        requiredPermissions: ["documents.cte.view"],
        description: "Documentos fiscais eletrônicos.",
      },
    ],
  },
  {
    id: "tracking",
    label: "Rastreamento",
    items: [
      {
        id: "positions",
        label: "Posições",
        href: "/m/tracking",
        icon: Gauge,
        requiredPermissions: ["tracking.position.view"],
        description: "Posição em tempo real da frota.",
      },
    ],
  },
  {
    id: "insights",
    label: "BI & IA",
    items: [
      {
        id: "dashboards",
        label: "Dashboards",
        href: "/m/dashboards",
        icon: LineChart,
        requiredPermissions: ["reporting.dashboard.view_own", "reporting.dashboard.view_shared"],
        description: "Dashboards e indicadores.",
      },
      {
        id: "ai-suggestions",
        label: "Sugestões de IA",
        href: "/m/ai-suggestions",
        icon: Bot,
        requiredPermissions: ["ai.suggestion.view"],
        description: "IA sugere; nunca decide (D161).",
      },
    ],
  },
  {
    id: "admin",
    label: "Administração",
    items: [
      {
        id: "users",
        label: "Usuários",
        href: "/usuarios",
        icon: Users,
        requiredPermissions: ["identity_access.user.view"],
        implemented: true,
        description: "Usuários do tenant.",
      },
      {
        id: "roles",
        label: "Papéis",
        href: "/papeis",
        icon: ShieldCheck,
        requiredPermissions: ["identity_access.role.view"],
        implemented: true,
        description: "RBAC — papéis e as permissões que cada um concede.",
      },
      {
        id: "permissions",
        label: "Permissões",
        href: "/permissoes",
        icon: ShieldCheck,
        requiredPermissions: ["identity_access.permission.view"],
        implemented: true,
        description: "Catálogo de permissões do sistema.",
      },
      {
        id: "branches",
        label: "Filiais",
        href: "/m/branches",
        icon: Building2,
        requiredPermissions: ["tenancy.branch.view"],
        description: "Filiais do tenant.",
      },
    ],
  },
];
