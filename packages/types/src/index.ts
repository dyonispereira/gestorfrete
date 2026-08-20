/**
 * Shared types mirroring `docs/api/openapi.yaml` (frozen, D427). Hand-kept in
 * this Lote — generating these from the OpenAPI document is a reasonable
 * future improvement, not attempted here to avoid adding a codegen step this
 * lote didn't ask for.
 */

export type UUID = string;
export type ISODateTime = string;

export interface AuditMetadata {
  created_at: ISODateTime;
  created_by?: UUID;
  updated_at: ISODateTime;
  updated_by?: UUID;
}

export type TenantStatus = "TRIAL" | "ATIVO" | "SUSPENSO" | "CANCELADO";
export type UserStatus = "ATIVO" | "INATIVO" | "BLOQUEADO";
export type SessionStatus = "ATIVA" | "EXPIRADA" | "ENCERRADA";

/** Returned inline by `GET /auth/me` — a narrower projection of `Tenant`. */
export interface TenantContext {
  id: UUID;
  codigo: string;
  razao_social: string;
  status: TenantStatus;
}

/** Returned by `GET /tenant`. */
export interface Tenant {
  id: UUID;
  codigo: string;
  razao_social: string;
  cnpj: string;
  status: TenantStatus;
  audit: AuditMetadata;
}

export interface Session {
  id: UUID;
  started_at: ISODateTime;
  expires_at: ISODateTime;
  status: SessionStatus;
}

export interface AuthUser {
  id: UUID;
  codigo: string;
  nome: string;
  email: string;
  status: UserStatus;
  driver_id?: UUID;
  employee_id?: UUID;
  /** Role UUIDs — resolve via `GET /roles/{id}` to get permission codes. */
  roles: UUID[];
  audit: AuditMetadata;
}

/** `GET /roles/{id}`. `permissions` is a flat array of RBAC codes (`modulo.recurso.acao`). */
export interface Role {
  id: UUID;
  codigo: string;
  nome: string;
  descricao?: string;
  permissions: string[];
  audit: AuditMetadata;
}

export interface Permission {
  id: UUID;
  code: string;
  name: string;
  module: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface LoginResponse extends AuthTokens {
  user: AuthUser;
}

export interface MeResponse {
  user: AuthUser;
  tenant: TenantContext;
  session: Session;
  /**
   * Role display names (not permission codes) — a display convenience, not a
   * substitute for resolving `user.roles` via `GET /roles/{id}`. See the
   * "Achado do Frontend Lote 1" note in `docs/api/001-authentication.md`.
   */
  roles: string[];
}

/** Envelope every non-2xx response uses (`ERROR_MODEL.md`). */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Array<{ field?: string; message: string }>;
    request_id?: string;
    correlation_id?: string;
  };
}

/**
 * Real shape of `meta.pagination` on every offset-paginated list endpoint
 * (`user_router.py`/`role_router.py`/`permission_router.py`) — `page`/
 * `limit`/`total`, NOT the `total_items`/`total_pages` that `PAGINATION.md`
 * describes. Follows the code, not the stale doc.
 */
export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: { pagination: PaginationMeta };
}

/** `GET /users` item shape is identical to `AuthUser` (`UserResponse = UserSummaryResponse` in the Backend). */
export type User = AuthUser;

export interface CreateUserRequest {
  nome: string;
  email: string;
  password: string;
  driver_id?: UUID;
  employee_id?: UUID;
  role_ids: UUID[];
}

export interface UpdateUserRequest {
  nome?: string;
  email?: string;
  role_ids?: UUID[];
}

export interface CreateRoleRequest {
  nome: string;
  descricao?: string;
  permissions: string[];
}

export interface UpdateRoleRequest {
  nome?: string;
  descricao?: string;
  permissions?: string[];
}

/* ── Cadastros (Cliente/Fornecedor/Motorista/Funcionário/Centro de Custo) ──
 * Field lists and enum values below are copied verbatim from the real
 * `*_schemas.py`/`*_status.py`/`*_type.py` files (Sprint 12, Lote Cadastros
 * audit) — never invented by analogy with another entity. Notably:
 * `EmployeeResponse` really has no phone/email/CPF; `CostCenter` really has
 * no DELETE and no way to list Filiais for `branch_id`; Address/Contact
 * list endpoints don't paginate for real despite returning the pagination
 * envelope shape. */

export type ClientStatus = "ATIVO" | "INATIVO";

export interface Client {
  id: UUID;
  codigo: string;
  razao_social: string;
  nome_fantasia?: string;
  document: string;
  telefone?: string;
  email?: string;
  status: ClientStatus;
  audit: AuditMetadata;
}

export interface CreateClientRequest {
  razao_social: string;
  nome_fantasia?: string;
  document: string;
  telefone?: string;
  email?: string;
}

export interface UpdateClientRequest {
  razao_social?: string;
  nome_fantasia?: string;
  telefone?: string;
  email?: string;
}

/** `contatos_cliente` — exclusive to Cliente, not polymorphic. No `audit.created_by/updated_by` (table has no such columns). */
export interface Contact {
  id: UUID;
  nome: string;
  cargo?: string;
  telefone?: string;
  email?: string;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface CreateContactRequest {
  nome: string;
  cargo?: string;
  telefone?: string;
  email?: string;
}

export interface UpdateContactRequest {
  nome?: string;
  cargo?: string;
  telefone?: string;
  email?: string;
}

/** `shared/addresses` — polymorphic across Cliente/Fornecedor (Filial has no router yet). No permission of its own; reuses the owner's `*.view`/`*.edit`. */
export type AddressType = "PRINCIPAL" | "COBRANCA" | "ENTREGA" | "OUTRO";

export interface Address {
  id: UUID;
  type: AddressType;
  logradouro: string;
  numero?: string;
  complemento?: string;
  bairro: string;
  cidade: string;
  uf: string;
  cep: string;
  audit: AuditMetadata;
}

export interface CreateAddressRequest {
  type: AddressType;
  logradouro: string;
  numero?: string;
  complemento?: string;
  bairro: string;
  cidade: string;
  uf: string;
  cep: string;
}

export interface UpdateAddressRequest {
  type?: AddressType;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
  cep?: string;
}

export type SupplierStatus = "ATIVO" | "INATIVO";
export type SupplierCategory =
  | "PECA"
  | "RECAPAGEM"
  | "SEGURO"
  | "OFICINA"
  | "POSTO"
  | "BORRACHARIA"
  | "GUINCHO"
  | "OUTRO";

export interface Supplier {
  id: UUID;
  codigo: string;
  razao_social: string;
  cnpj: string;
  telefone?: string;
  category?: SupplierCategory;
  status: SupplierStatus;
  audit: AuditMetadata;
}

export interface CreateSupplierRequest {
  razao_social: string;
  cnpj: string;
  telefone?: string;
  category?: SupplierCategory;
}

export interface UpdateSupplierRequest {
  razao_social?: string;
  telefone?: string;
  category?: SupplierCategory;
}

export type DriverEmploymentType = "EMPREGADO" | "AUTONOMO";
/** Computed by `block()`/`unblock()` — never accepted in a create/update body. */
export type DriverFitnessStatus = "APTO" | "BLOQUEADO";

export interface Driver {
  id: UUID;
  codigo: string;
  nome: string;
  cpf: string;
  telefone?: string;
  email?: string;
  employment_type: DriverEmploymentType;
  fitness_status: DriverFitnessStatus;
  audit: AuditMetadata;
}

export interface CreateDriverRequest {
  nome: string;
  cpf: string;
  telefone?: string;
  email?: string;
  employment_type: DriverEmploymentType;
}

export interface UpdateDriverRequest {
  nome?: string;
  telefone?: string;
  email?: string;
}

export type DriverDocumentType = "CNH" | "RG" | "EXAME_TOXICOLOGICO" | "REGISTRO_ANTT";
export type CnhCategory = "A" | "B" | "C" | "D" | "E";
/** Computed from `expires_at` on read — never accepted in a create/update body. */
export type DriverDocumentStatus = "VALIDO" | "VENCIDO";

export interface DriverDocument {
  id: UUID;
  type: DriverDocumentType;
  number: string;
  cnh_category?: CnhCategory;
  expires_at?: string;
  status: DriverDocumentStatus;
}

export interface CreateDriverDocumentRequest {
  type: DriverDocumentType;
  number: string;
  cnh_category?: CnhCategory;
  expires_at?: string;
}

export interface UpdateDriverDocumentRequest {
  number?: string;
  cnh_category?: CnhCategory;
  expires_at?: string;
}

export type EmployeeStatus = "ATIVO" | "INATIVO";

/** Leanest of the Cadastros entities — really has no phone/email/CPF/address/contact/documents. */
export interface Employee {
  id: UUID;
  codigo: string;
  nome: string;
  cargo: string;
  hired_at?: string;
  status: EmployeeStatus;
  audit: AuditMetadata;
}

export interface CreateEmployeeRequest {
  nome: string;
  cargo: string;
  hired_at?: string;
}

export interface UpdateEmployeeRequest {
  nome?: string;
  cargo?: string;
  hired_at?: string;
}

export type CostCenterStatus = "ATIVO" | "INATIVO";

export interface CostCenter {
  id: UUID;
  codigo: string;
  accounting_code: string;
  nome: string;
  branch_id?: UUID;
  status: CostCenterStatus;
  audit: AuditMetadata;
}

/** No `branch_id` in the create form — no endpoint exists to list Filiais to pick from (see Lote Cadastros plan). */
export interface CreateCostCenterRequest {
  accounting_code: string;
  nome: string;
}

export interface UpdateCostCenterRequest {
  nome?: string;
  status?: CostCenterStatus;
}
