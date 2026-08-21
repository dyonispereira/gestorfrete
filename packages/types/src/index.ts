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

/* ── Frota (Veículo/Implemento/Composição/Hodômetro/Disponibilidade) ──
 * Field lists and enum values copied verbatim from the real
 * `*_schemas.py`/domain `value_objects/*.py` files (Sprint 12, Lote Frota
 * audit). Notably: `Vehicle.operational` is ALWAYS empty (never populated by
 * create/update) — always fetch `/veiculos/{id}/disponibilidade` for real
 * status, never read this field. Composição has no PATCH/DELETE — D248,
 * "editing" is POST-ing a whole new composition (server auto-closes the
 * previous one). Odometer readings have no PATCH/DELETE either, and use
 * cursor pagination, not offset. Availability is a pure read model — no
 * write endpoint exists anywhere. Vehicle Document `type` is an unvalidated
 * free string server-side despite looking like it should be an enum. */

export type VehicleStatus = "ATIVO" | "INATIVO";
export type FuelType = "DIESEL_S10" | "DIESEL_S500" | "GNV" | "ELETRICO";
export type AvailabilityStatus = "DISPONIVEL" | "EM_VIAGEM" | "EM_MANUTENCAO" | "INATIVO";
export type VehicleDocumentStatus = "VALIDO" | "VENCIDO";
export type BodyType = "CARRETA" | "TANQUE" | "BAU" | "GRANELEIRO" | "PRANCHA" | "FRIGORIFICO" | "GAIOLA";
export type ImplementAvailability = "DISPONIVEL" | "EM_USO" | "INATIVO";
export type CombinationType = "SIMPLES" | "BITREM" | "RODOTREM";
export type CompositionStatus = "VALIDA" | "INVALIDA";
export type OdometerOrigin = "ABASTECIMENTO" | "CHECKLIST" | "MANUAL" | "TELEMETRIA";

/** Always empty — `CreateVehicleHandler`/`UpdateVehicleHandler` never populate it. */
export interface VehicleOperational {
  status?: string;
  current_driver_id?: UUID;
  current_implement_id?: UUID;
  updated_at?: string;
}

export interface Vehicle {
  id: UUID;
  identity: { codigo: string; plate: string; renavam: string };
  status: VehicleStatus;
  branch_id?: UUID;
  operational: VehicleOperational;
  audit: AuditMetadata;
}

export interface CreateVehicleRequest {
  plate: string;
  renavam: string;
  fabricante: string;
  modelo: string;
  ano_fabricacao: number;
  categoria_id: UUID;
  branch_id?: UUID;
}

export interface UpdateVehicleRequest {
  fabricante?: string;
  modelo?: string;
  ano_fabricacao?: number;
  categoria_id?: UUID;
  branch_id?: UUID;
}

export interface VehicleTechnicalSheet {
  id: UUID;
  manufacturer: string;
  model: string;
  manufacture_year: number;
  category_id: UUID;
  chassis: string;
  engine?: string;
  axles: number;
  tare_weight: string;
  load_capacity: string;
  gross_vehicle_weight: string;
  owner_rntrc?: string;
  fuel_type: FuelType;
}

export interface UpsertVehicleTechnicalSheetRequest {
  chassis?: string;
  engine?: string;
  axles?: number;
  tare_weight?: string;
  load_capacity?: string;
  gross_vehicle_weight?: string;
  owner_rntrc?: string;
  fuel_type?: FuelType;
}

/** `type` is a free string server-side — no enum/vocabulary validation despite looking like one. */
export interface VehicleDocument {
  id: UUID;
  type: string;
  number: string;
  expires_at: string;
  status: VehicleDocumentStatus;
  file_id?: UUID;
}

export interface CreateVehicleDocumentRequest {
  type: string;
  number: string;
  expires_at: string;
  file_id?: UUID;
}

export interface UpdateVehicleDocumentRequest {
  number?: string;
  expires_at?: string;
  file_id?: UUID;
}

export interface Implement {
  id: UUID;
  codigo: string;
  plate: string;
  renavam: string;
  body_type: BodyType;
  category_id: UUID;
  load_capacity: string;
  availability_status: ImplementAvailability;
}

export interface CreateImplementRequest {
  plate: string;
  renavam: string;
  body_type: BodyType;
  category_id: UUID;
  load_capacity: string;
}

export interface UpdateImplementRequest {
  body_type?: BodyType;
  load_capacity?: string;
  availability_status?: ImplementAvailability;
}

/** No PATCH/DELETE anywhere (D248) — only POST (new) and POST .../commands/validate. */
export interface VehicleComposition {
  id: UUID;
  tractor_unit_id: UUID;
  combination_type: CombinationType;
  total_axles: number;
  status: CompositionStatus;
  implements: Array<{ implement_id: UUID; order: number }>;
  starts_at: ISODateTime;
  ends_at?: ISODateTime;
}

export interface CreateVehicleCompositionRequest {
  tractor_unit_id: UUID;
  combination_type: CombinationType;
  total_axles: number;
  implements: Array<{ implement_id: UUID; order: number }>;
}

/** No PATCH/DELETE — append-only Time Series. */
export interface OdometerReading {
  id: UUID;
  value_km: string;
  origin: OdometerOrigin;
  trip_id?: UUID;
  captured_at: ISODateTime;
}

export interface CreateOdometerReadingRequest {
  value_km: string;
  origin: OdometerOrigin;
  trip_id?: UUID;
}

/** Cursor-paginated, unlike every other list in the app (offset `page/limit/total`). */
export interface CursorPaginatedResponse<T> {
  data: T[];
  meta: { pagination: { next_cursor?: string; has_more: boolean } };
}

/**
 * Pure read model — no write endpoint exists anywhere for this resource. The
 * projector that computes it is not yet wired to real trip/maintenance
 * events in this environment (Lote Frota audit) — data may lag behind
 * actual operations; still real API data, just show it as-is.
 */
export interface VehicleAvailability {
  vehicle_id: UUID;
  status: AvailabilityStatus;
  current_driver_id?: UUID;
  current_implement_id?: UUID;
  updated_at: ISODateTime;
}

/* ── Operação (Viagem/Entrega/Ocorrência/Canhoto/Alocação/Timeline/Comentários/Anexos) ──
 * Field lists and enum values copied verbatim from the real `*_schemas.py`/domain
 * `value_objects/*.py` files (Sprint 13, Lote Operação audit). Notably: Trip status is
 * command-only — `PATCH /viagens/{id}` only touches `data_programada`/`janela_programada`, never
 * `status`; every transition is a `POST .../commands/<verb>`. `references.*` are live entity IDs;
 * `snapshots.*` freeze at creation (`client_snapshot`) or dispatch (`driver_name_snapshot`/
 * `tractor_unit_plate_snapshot`) and never re-sync. `financials.*`/`status.fiscal`/
 * `status.financial` are always readOnly — driven by future `documents`/`financial` module
 * events, no command sets them directly. Delivery `status` IS directly PATCH-editable (the one
 * exception to command-only). No DELETE exists anywhere in this module except `DELETE /viagens/
 * {id}` itself (blocked outside RASCUNHO/PLANEJADA). ProofOfDelivery and TripStatusHistoryEntry
 * have no update method at all once created — immutable. TripAllocation is append-only: `POST
 * /resources` only works once, `POST .../commands/reallocate-resources` supersedes it (old row →
 * SUBSTITUIDA, new row inserted), never PATCH/DELETE. Timeline is GET-only, forever (D187/D236). */

export type TripOperationalStatus =
  | "RASCUNHO"
  | "PLANEJADA"
  | "AGUARDANDO_CHECKLIST"
  | "LIBERADA"
  | "EM_DESLOCAMENTO"
  | "CARREGANDO"
  | "EM_TRANSITO"
  | "EM_ENTREGA"
  | "FINALIZADA"
  | "INTERROMPIDA"
  | "CANCELADA";

export type TripFiscalStatus = "PENDENTE" | "CTE_EMITIDO" | "MDFE_EMITIDO" | "MDFE_ENCERRADO" | "CTE_CANCELADO";
export type TripFinancialStatus = "AGUARDANDO_FATURAMENTO" | "FATURADA" | "AGUARDANDO_RECEBIMENTO" | "RECEBIDA";
export type DeliveryStatus = "PENDENTE" | "CONCLUIDA" | "RECUSADA" | "DEVOLVIDA" | "CANCELADA";
export type OccurrenceType = "ATRASO" | "AVARIA" | "PANE" | "SINISTRO" | "OUTRO";
export type OccurrenceSeverity = "BAIXA" | "MEDIA" | "ALTA" | "CRITICA";
export type OccurrenceStatus = "ABERTA" | "RESOLVIDA";
export type ProofOfDeliveryStatus = "PENDENTE" | "REGISTRADO";
export type AllocationStatus = "VIGENTE" | "SUBSTITUIDA";

export interface TripReferences {
  client_id: UUID;
  driver_id?: UUID;
  tractor_unit_id?: UUID;
}

export interface TripSnapshots {
  driver_name_snapshot?: string;
  tractor_unit_plate_snapshot?: string;
  client_snapshot?: Record<string, unknown>;
  predicted_revenue_snapshot?: string;
  applied_price_table_id?: UUID;
}

export interface TripStatus {
  operational: TripOperationalStatus;
  fiscal: TripFiscalStatus;
  financial: TripFinancialStatus;
  closed: boolean;
}

export interface TripFinancials {
  predicted_cost?: string;
  actual_cost?: string;
  actual_revenue?: string;
  predicted_margin?: string;
  actual_margin?: string;
  financial_deviation?: string;
}

export interface Trip {
  id: UUID;
  codigo: string;
  scheduled_date?: string;
  scheduled_window?: ISODateTime;
  references: TripReferences;
  snapshots: TripSnapshots;
  status: TripStatus;
  financials: TripFinancials;
  distance_traveled_km?: string;
  audit: AuditMetadata;
}

export interface CreateTripRequest {
  cliente_id: UUID;
  data_programada?: string;
  janela_programada?: ISODateTime;
}

export interface UpdateTripRequest {
  data_programada?: string;
  janela_programada?: ISODateTime;
}

export interface InterromperTripRequest {
  notes: string;
}

export interface CancelarTripRequest {
  notes: string;
}

export interface CloseAdministrativeTripRequest {
  justification: string;
}

/** Atomic package (driver+tractor+implement) — never edited in place (D188), see module doc above. */
export interface TripAllocation {
  id: UUID;
  driver_id: UUID;
  tractor_unit_id: UUID;
  implement_id?: UUID;
  status: AllocationStatus;
  replacement_reason?: string;
  created_at: ISODateTime;
}

export interface CreateTripAllocationRequest {
  driver_id: UUID;
  tractor_unit_id: UUID;
  implement_id?: UUID;
}

export interface ReallocateTripResourcesRequest {
  driver_id: UUID;
  tractor_unit_id: UUID;
  implement_id?: UUID;
  reason: string;
}

export interface DeliveryWindow {
  starts_at: ISODateTime;
  ends_at: ISODateTime;
}

/** No `audit` — `entregas` has no timestamp/actor columns at all (D381). */
export interface Delivery {
  id: UUID;
  order: number;
  recipient: string;
  delivery_address: Record<string, unknown>;
  status: DeliveryStatus;
  completed_at?: ISODateTime;
  rejection_reason?: string;
  window?: DeliveryWindow;
}

export interface CreateDeliveryRequest {
  order: number;
  recipient: string;
  delivery_address: Record<string, unknown>;
  window?: DeliveryWindow;
}

export interface UpdateDeliveryRequest {
  recipient?: string;
  delivery_address?: Record<string, unknown>;
  status?: DeliveryStatus;
  rejection_reason?: string;
}

/** No `update()` at all — immutable once registered (1:1 with Delivery). */
export interface ProofOfDelivery {
  id: UUID;
  status: ProofOfDeliveryStatus;
  registered_at?: ISODateTime;
  signature_file_id?: UUID;
}

export interface RegisterProofOfDeliveryRequest {
  signature_file_id?: UUID;
}

/** No `audit`. `location` is accepted on create but not persisted — no column exists (documented gap). */
export interface Occurrence {
  id: UUID;
  type: OccurrenceType;
  description: string;
  severity?: OccurrenceSeverity;
  status: OccurrenceStatus;
  occurred_at: ISODateTime;
}

export interface CreateOccurrenceRequest {
  type: OccurrenceType;
  description: string;
  severity?: OccurrenceSeverity;
  occurred_at: ISODateTime;
  location?: { latitude: number; longitude: number };
}

export interface UpdateOccurrenceRequest {
  description?: string;
  severity?: OccurrenceSeverity;
  status?: OccurrenceStatus;
}

/**
 * `GET /viagens/{id}/financeiro` (D389) — individual field groups are `null` when the actor
 * lacks the matching permission (`financial.trip_predicted_value.view` / `_actual_value.view` /
 * `_margin.view`), never a partial `403`. Render `null` as "—", not as missing/broken data.
 */
export interface TripFinancialsView {
  financial_status: TripFinancialStatus;
  predicted_revenue?: string;
  predicted_cost?: string;
  predicted_margin?: string;
  actual_revenue?: string;
  actual_cost?: string;
  actual_margin?: string;
  financial_deviation?: string;
}

/** Cursor-paginated, GET-only forever (D187/D236) — merges status history + occurrences + comments/attachments. */
export interface TripTimelineEntry {
  occurred_at: ISODateTime;
  source: string;
  summary: string;
  reference_id: UUID;
}

/** `comentarios` has no real update timestamp — `audit.updated_at`/`updated_by` always mirror `created_at`/`created_by` even after a real PATCH (D400/D381-family). */
export interface TripComment {
  id: UUID;
  text: string;
  visible_to_client: boolean;
  author_id: UUID;
  audit: AuditMetadata;
}

export interface CreateCommentRequest {
  text: string;
  visible_to_client?: boolean;
}

export interface UpdateCommentRequest {
  text?: string;
  visible_to_client?: boolean;
}

/** `anexos` has no `atualizado_em`/`atualizado_por` — immutable, same audit-mirroring caveat as Comment. */
export interface TripAttachment {
  id: UUID;
  attachment_type: string;
  file_id: UUID;
  description?: string;
  audit: AuditMetadata;
}

export interface CreateAttachmentRequest {
  attachment_type: string;
  file_id: UUID;
  description?: string;
}
