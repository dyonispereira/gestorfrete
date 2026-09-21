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

/* ── Financeiro (Contas a Pagar/Receber, Faturas, Plano de Contas, Contas Bancárias, Estornos) ──
 * Sprint 15, Lote Financeiro, Parte 2. Backend congelado desde a Parte 1 — só consumindo o
 * contrato existente aqui, nenhuma invenção de campo. `FinancialReversal` não expõe quem fez o
 * estorno (sem `actor`/`usuario_id` no contrato) — gap real registrado, não meio-inventado aqui. */

export type PayableOrigin = "VIAGEM" | "ORDEM_SERVICO" | "ABASTECIMENTO" | "COMPRA" | "AJUSTE_MANUAL";
export type PayableStatus = "LANCADA" | "AGUARDANDO_APROVACAO" | "APROVADA" | "PAGA" | "CONCILIADA" | "REJEITADA";
export type ExpenseApprovalDecision = "APROVADO" | "REJEITADO";
export type ExpenseAllocationCriterion = "KM_RODADO" | "NUMERO_VIAGENS" | "PESO_TRANSPORTADO";

export interface AccountsPayable {
  id: UUID;
  supplier_id: UUID;
  cost_center_id: UUID;
  origin: PayableOrigin;
  trip_id?: UUID;
  maintenance_order_id?: UUID;
  vehicle_id?: UUID;
  driver_id?: UUID;
  value: string;
  due_date: string;
  accounting_period: string;
  chart_of_accounts_id: UUID;
  status: PayableStatus;
  audit: AuditMetadata;
}

export interface CreateAccountsPayableRequest {
  supplier_id: UUID;
  cost_center_id: UUID;
  origin: PayableOrigin;
  trip_id?: UUID;
  maintenance_order_id?: UUID;
  vehicle_id?: UUID;
  driver_id?: UUID;
  value: string;
  due_date: string;
  accounting_period: string;
  chart_of_accounts_id: UUID;
}

export interface UpdateAccountsPayableRequest {
  supplier_id?: UUID;
  cost_center_id?: UUID;
  value?: string;
  due_date?: string;
  chart_of_accounts_id?: UUID;
}

export interface ExpenseDecisionRequest {
  justification?: string;
}

export interface PayAccountsPayableRequest {
  bank_account_id: UUID;
}

export interface ExpenseApproval {
  id: UUID;
  decision: ExpenseApprovalDecision;
  justification?: string;
  actor_id: UUID;
  decided_at: ISODateTime;
}

export interface ExpenseAllocation {
  id: UUID;
  cost_center_id?: UUID;
  trip_id?: UUID;
  criterion: ExpenseAllocationCriterion;
  allocated_value: string;
}

export type InvoiceStatus = "EMITIDA" | "CANCELADA";

export interface Invoice {
  id: UUID;
  invoice_number: string;
  trip_id?: UUID;
  delivery_id?: UUID;
  client_id: UUID;
  total_value: string;
  issue_date: string;
  payment_method_id: UUID;
  status: InvoiceStatus;
  audit: AuditMetadata;
}

export interface InvoiceInstallmentRequest {
  value: string;
  due_date: string;
  accounting_period: string;
}

export interface CreateInvoiceRequest {
  trip_id?: UUID;
  delivery_id?: UUID;
  client_id: UUID;
  total_value: string;
  payment_method_id: UUID;
  installments: InvoiceInstallmentRequest[];
}

export type ReceivableStatus = "PENDENTE" | "VENCIDA" | "RECEBIDA" | "CONCILIADA";

export interface AccountsReceivable {
  id: UUID;
  installment_number: number;
  value: string;
  due_date: string;
  accounting_period: string;
  received_at?: ISODateTime;
  status: ReceivableStatus;
}

export interface CreateAccountsReceivableRequest {
  value: string;
  due_date: string;
  accounting_period: string;
}

export interface UpdateAccountsReceivableRequest {
  value?: string;
  due_date?: string;
}

export interface ConfirmReceiptRequest {
  received_value: string;
}

export type ChartOfAccountsType = "RECEITA" | "DESPESA";
export type ChartOfAccountsStatus = "ATIVO" | "INATIVO";

export interface ChartOfAccounts {
  id: UUID;
  account_code: string;
  name: string;
  type: ChartOfAccountsType;
  parent_id?: UUID;
  status: ChartOfAccountsStatus;
  audit: AuditMetadata;
}

export interface CreateChartOfAccountsRequest {
  account_code: string;
  name: string;
  type: ChartOfAccountsType;
  parent_id?: UUID;
}

export interface UpdateChartOfAccountsRequest {
  name?: string;
  parent_id?: UUID;
  status?: ChartOfAccountsStatus;
}

export type BankAccountType = "CORRENTE" | "POUPANCA";
export type BankAccountStatus = "ATIVA" | "INATIVA";

export interface BankAccount {
  id: UUID;
  bank: string;
  branch: string;
  account_number: string;
  type: BankAccountType;
  status: BankAccountStatus;
  audit: AuditMetadata;
}

export interface BankAccountBalance {
  bank_account_id: UUID;
  balance: string;
  calculated_at: ISODateTime;
}

export interface CreateBankAccountRequest {
  bank: string;
  branch: string;
  account_number: string;
  type: BankAccountType;
}

export interface UpdateBankAccountRequest {
  bank?: string;
  branch?: string;
  status?: BankAccountStatus;
}

export interface FinancialReversal {
  id: UUID;
  invoice_id?: UUID;
  accounts_payable_id?: UUID;
  accounts_receivable_id?: UUID;
  value: string;
  reason: string;
  reversed_at: ISODateTime;
}

export interface CreateFinancialReversalRequest {
  invoice_id?: UUID;
  accounts_payable_id?: UUID;
  accounts_receivable_id?: UUID;
  value: string;
  reason: string;
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
export type OdometerOrigin = "ABASTECIMENTO" | "CHECKLIST" | "MANUAL" | "TELEMETRIA" | "ORDEM_SERVICO";

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

/* ── Documentos Fiscais (CT-e/MDF-e/Carta de Correção/NF-e Referenciada/Configuração Fiscal/
 * Eventos Fiscais) ── Field lists and enum values copied verbatim from the real
 * `*_schemas.py`/domain `value_objects/*.py` files (Sprint 14, Lote Documentos Fiscais audit).
 * CIOT is deliberately out of scope — `MODULE_PRIORITY.md` places it in V2 even though its
 * backend already exists; no CIOT types here. Notably: there is no `POST /ctes` — a CT-e is only
 * ever auto-created by `freight`'s `DispatchTripHandler` on trip dispatch (D396), which is itself
 * unreachable via this UI today (Lote Operação found `LIBERADA` has no path in). Every status
 * transition is `POST .../commands/<verbo>`, never PATCH (D274). CT-e/MDF-e rows are never
 * deleted, even cancelled/inutilized (D109). `AUTORIZADO`/`DENEGADO` (CT-e) and `PENDENTE→
 * AUTORIZADO` (MDF-e) are only reachable via a test-only SEFAZ-response simulator with no HTTP
 * path (D397) — a CT-e built through this UI can never progress past `TRANSMITIDO` in this
 * environment. `mdfes`/`ciots`/`configuracoes_fiscais_tenant` have no `audit`/timestamp columns
 * at all in the frozen DDL (D400) — omitted here, never fabricated. */

export type CteStatus = "RASCUNHO" | "VALIDADO" | "ASSINADO" | "TRANSMITIDO" | "AUTORIZADO" | "CANCELADO" | "DENEGADO" | "INUTILIZADO";
export type MdfeStatus = "PENDENTE" | "AUTORIZADO" | "ENCERRADO" | "CANCELADO";
export type FiscalConfigurationEnvironment = "PRODUCAO" | "HOMOLOGACAO";
export type FiscalConfigurationStatus = "ATIVA" | "INATIVA";
export type FiscalEventDocumentType = "CTE" | "MDFE" | "CIOT";
export type FiscalEventType = "REQUISICAO" | "RESPOSTA";
export type FiscalEventResult = "SUCESSO" | "FALHA" | "TIMEOUT";

/** D400 — `ctes` só tem `criado_em`/`atualizado_em`; `created_by`/`updated_by` sempre `null`. */
export interface Cte {
  id: UUID;
  trip_id: UUID;
  number: string;
  series: string;
  access_key?: string;
  service_value: string;
  status: CteStatus;
  xml_file_id?: UUID;
  sefaz_protocol?: string;
  authorized_at?: ISODateTime;
  audit: AuditMetadata;
}

export interface CancelCteRequest {
  notes: string;
}

/** Sem `audit` — `mdfes` não tem nenhuma coluna de timestamp na DDL congelada (D400). */
export interface Mdfe {
  id: UUID;
  trip_id: UUID;
  number: string;
  series: string;
  access_key?: string;
  status: MdfeStatus;
  cte_ids: UUID[];
  xml_file_id?: UUID;
  sefaz_protocol?: string;
  closed_at?: ISODateTime;
}

export interface CreateMdfeRequest {
  trip_id: UUID;
  cte_ids: UUID[];
}

export interface CancelMdfeRequest {
  notes: string;
}

/** Compartilhado por CT-e/MDF-e status-history (D284) — cursor-paginado, GET-only para sempre. */
export interface StatusHistoryEntry {
  id: UUID;
  status: string;
  user_id?: UUID;
  origin: string;
  notes?: string;
  occurred_at: ISODateTime;
}

/** D276 — nunca o XML embutido, só a referência ao artefato em Storage; sem endpoint de download binário ainda. */
export interface XmlReference {
  xml_file_id: UUID;
  generated_at?: ISODateTime;
}

/** Só aceita com CT-e pai AUTORIZADO (D282) — append-only, sem edição/exclusão. */
export interface CorrectionLetter {
  id: UUID;
  sequence_number: number;
  correction_text: string;
  xml_file_id?: UUID;
  sent_at: ISODateTime;
}

export interface CreateCorrectionLetterRequest {
  correction_text: string;
}

/** Sem gate de status do CT-e pai — append-only, sem edição/exclusão. */
export interface ReferencedNfe {
  id: UUID;
  access_key: string;
  xml_file_id?: UUID;
}

export interface CreateReferencedNfeRequest {
  access_key: string;
}

/** Sem `audit` — `configuracoes_fiscais_tenant` não tem coluna de timestamp na DDL congelada (D400). Singular por tenant. */
export interface FiscalConfiguration {
  id: UUID;
  certificate_file_id: UUID;
  certificate_expires_at: string;
  environment: FiscalConfigurationEnvironment;
  tax_regime: string;
  cte_series: string;
  next_cte_number: number;
  mdfe_series: string;
  next_mdfe_number: number;
  status: FiscalConfigurationStatus;
}

/**
 * `PATCH` — cada campo exige sua própria permissão (D267-style); enviar um campo sem a permissão
 * correspondente rejeita a requisição inteira, nunca um PATCH parcialmente aplicado:
 * `tax_regime`→`documents.fiscal_config.edit`; `certificate_file_id`/`certificate_expires_at`→
 * `documents.fiscal_config.manage_certificate`; `cte_series`/`mdfe_series`→
 * `documents.fiscal_config.manage_series`; `environment`→`documents.fiscal_config.switch_environment`.
 */
export interface UpdateFiscalConfigurationRequest {
  tax_regime?: string;
  certificate_file_id?: UUID;
  certificate_expires_at?: string;
  cte_series?: string;
  mdfe_series?: string;
  environment?: FiscalConfigurationEnvironment;
}

/**
 * D277 — somente leitura para usuários, todo campo readOnly. Log técnico bruto (D105), distinto
 * dos `*StatusHistory` de negócio — em ambientes sem o simulador de resposta SEFAZ acionado, esta
 * lista fica vazia (nada no caminho HTTP alcançável grava uma linha aqui).
 */
export interface FiscalEvent {
  id: UUID;
  document_type: FiscalEventDocumentType;
  document_id: UUID;
  event_type: FiscalEventType;
  payload_file_id: UUID;
  external_protocol?: string;
  started_at: ISODateTime;
  finished_at?: ISODateTime;
  duration_ms?: number;
  attempt_number: number;
  result?: FiscalEventResult;
  origin: string;
}

/* ── Manutenção — Checklist (desbloqueia Trip.AGUARDANDO_CHECKLIST → LIBERADA) ──
 * Sprint 15, Lote Frota e Manutenção (Parte 1). Formalizada como entidade só nesta Lote — não
 * existia no Modelo de Domínio até agora (ver `docs/domain/004-manutencao.md`). Sem "Modelo de
 * Checklist" configurável: `items` é armazenado inline, sem template/versionamento próprios.
 * `POST /checklists` é o gatilho de `PLANEJADA→AGUARDANDO_CHECKLIST` (não o preenchimento), e
 * `commands/approve` é o gatilho real de `AGUARDANDO_CHECKLIST→LIBERADA` — os dois já existiam
 * como métodos internos em `freight.TripInternalTransitions` (D376), só nunca tinham sido
 * chamados. Um `Aprovado`/`Reprovado` nunca é reaberto; reprovar sempre cria um novo checklist
 * `Pendente` referenciando o reprovado. `Referencia_tipo=ORDEM_SERVICO` já existe no vocabulário
 * mas não tem suporte no Backend ainda (Ordem de Serviço é a Parte 2 desta Lote). */

export type ChecklistType = "MOTORISTA_SAIDA" | "MOTORISTA_RETORNO" | "OFICINA" | "ADMINISTRATIVO" | "CARREGAMENTO" | "DESCARGA";
export type ChecklistReferenceType = "VIAGEM" | "ORDEM_SERVICO";
export type ChecklistStatus = "PENDENTE" | "EM_PREENCHIMENTO" | "CONCLUIDO" | "APROVADO" | "REPROVADO";

export interface ChecklistItem {
  descricao: string;
  critico: boolean;
  resposta?: boolean;
}

export interface Checklist {
  id: UUID;
  codigo: string;
  type: ChecklistType;
  reference_type: ChecklistReferenceType;
  reference_id: UUID;
  tractor_unit_id: UUID;
  driver_id?: UUID;
  items: ChecklistItem[];
  status: ChecklistStatus;
  rejected_checklist_id?: UUID;
  audit: AuditMetadata;
}

export interface CreateChecklistRequest {
  type: ChecklistType;
  reference_type: ChecklistReferenceType;
  reference_id: UUID;
}

export interface SubmitChecklistRequest {
  itens: ChecklistItem[];
}

export interface RejectChecklistRequest {
  observacao: string;
}

/* ── Manutenção — Ordem de Serviço (núcleo: OS/Item/Aprovação de Custo) ──
 * Sprint 15, Lote Frota e Manutenção, Parte 2. DDL já estava congelada em `docs/database/
 * relational/005-manutencao.md` antes desta Lote — só o núcleo (`maintenance.work_order.*`/
 * `.work_order_item.*`/`.cost_approval.*`) é implementado agora; Estoque/Solicitação de Peça/
 * Plano Preventivo ficam para depois (RBAC groups próprios, deliberadamente fora de escopo).
 * `AGUARDANDO_PECA` existe no enum mas não é alcançável ainda — depende do subsistema de peças.
 * `necessita_aprovacao` é informado explicitamente no diagnóstico (a alçada configurável por
 * tenant, em `settings`, ainda não existe). `custo_previsto`/`custo_realizado` nunca são
 * digitados — recalculados pelo Backend a partir dos itens. */

export type WorkOrderType = "PREVENTIVA" | "CORRETIVA" | "EMERGENCIAL" | "GARANTIA";
export type WorkOrderOpeningOrigin = "MANUAL" | "MANUTENCAO_PREVENTIVA_SUGERIDA" | "VIAGEM_INTERROMPIDA" | "CHECKLIST_REPROVADO" | "SUGESTAO_IA";
export type WorkOrderCause = "DESGASTE" | "QUEBRA" | "ACIDENTE" | "MAU_USO" | "INSPECAO" | "RECALL";
export type WorkOrderStatus = "ABERTA" | "EM_DIAGNOSTICO" | "AGUARDANDO_APROVACAO" | "AGUARDANDO_PECA" | "EM_EXECUCAO" | "CONCLUIDA" | "FECHADA" | "CANCELADA";
export type WorkOrderItemCostCategory = "PECAS" | "PNEUS" | "SERVICOS" | "TERCEIROS" | "MAO_DE_OBRA_INTERNA" | "MAO_DE_OBRA_TERCEIRIZADA" | "DESLOCAMENTO" | "OUTROS";
export type CostApprovalDecision = "APROVADO" | "REJEITADO";

export interface WorkOrder {
  id: UUID;
  codigo: string;
  tractor_unit_id: UUID;
  composition_id?: UUID;
  supplier_id?: UUID;
  type: WorkOrderType;
  opening_origin: WorkOrderOpeningOrigin;
  problem_description: string;
  cause?: WorkOrderCause;
  root_cause?: string;
  technical_diagnosis?: string;
  mechanic_id?: UUID;
  predicted_cost?: string;
  actual_cost?: string;
  needs_approval: boolean;
  completion_evidence_required: boolean;
  status: WorkOrderStatus;
  execution_started_at?: ISODateTime;
  completed_at?: ISODateTime;
  opening_odometer_km?: string;
  completion_odometer_km?: string;
  cost_center_id?: UUID;
  chart_of_accounts_id?: UUID;
  audit: AuditMetadata;
}

export interface CreateWorkOrderRequest {
  tractor_unit_id: UUID;
  type: WorkOrderType;
  problem_description: string;
  composition_id?: UUID;
  supplier_id?: UUID;
  opening_odometer_km?: string;
  cost_center_id?: UUID;
  chart_of_accounts_id?: UUID;
}

export interface ConcludeWorkOrderRequest {
  completion_odometer_km?: string;
}

export interface DiagnoseWorkOrderRequest {
  technical_diagnosis?: string;
  cause?: WorkOrderCause;
  root_cause?: string;
  mechanic_id?: UUID;
  needs_approval?: boolean;
}

export interface ApproveCostRequest {
  justification?: string;
}

export interface RejectCostRequest {
  justification: string;
}

export interface CancelWorkOrderRequest {
  justification: string;
}

export interface WorkOrderItem {
  id: UUID;
  ordem_servico_id: UUID;
  cost_category: WorkOrderItemCostCategory;
  description: string;
  part_stock_id?: UUID;
  quantity: string;
  unit_value: string;
  total_value: string;
}

export interface CreateWorkOrderItemRequest {
  cost_category: WorkOrderItemCostCategory;
  description: string;
  quantity: string;
  unit_value: string;
  part_stock_id?: UUID;
}

export interface CostApproval {
  id: UUID;
  ordem_servico_id: UUID;
  level: number;
  decision: CostApprovalDecision;
  justification?: string;
  actor_id: UUID;
  occurred_at: ISODateTime;
}
