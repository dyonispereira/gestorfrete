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
