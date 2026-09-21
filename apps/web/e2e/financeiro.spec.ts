import { execFileSync } from "node:child_process";

import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";
const CATEGORY_ID = "f14a0000-0000-0000-0000-0000000000c1";
const PAYMENT_METHOD_ID = "f14a0000-0000-0000-0000-0000000000f1";
const CONTAINER = process.env.E2E_POSTGRES_CONTAINER ?? "gestorfrete-postgres-1";
const DB_USER = process.env.E2E_POSTGRES_USER ?? "gestorfrete";
const DB_NAME = process.env.E2E_POSTGRES_DB ?? "gestorfrete";
// `request` (Node-side, no browser) does not go through the Next.js dev server's origin the way
// `page` does — `apiFetch` in the browser calls `NEXT_PUBLIC_API_URL` directly, so API calls made
// from `request` need that same absolute backend origin, not the Playwright `baseURL` (the frontend).
const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1`;

async function getAuthToken(request: APIRequestContext, email: string): Promise<string> {
  const response = await request.post(`${API_BASE_URL}/auth/login`, { data: { email, password: PASSWORD } });
  const body = (await response.json()) as { access_token: string };
  return body.access_token;
}

async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
  await page.fill("#email", email);
  await page.fill("#password", PASSWORD);
  await page.click("button[type=submit]");
  await page.waitForURL("**/dashboard");
}

function uniqueDigits(length: number): string {
  return Date.now().toString().padStart(length, "0").slice(-length);
}

async function createClient(page: Page, name: string) {
  await page.goto("/clientes");
  await page.getByRole("button", { name: "Novo cliente" }).click();
  await page.fill("#client-razao-social", name);
  await page.fill("#client-document", uniqueDigits(14));
  await page.getByRole("button", { name: "Criar cliente" }).click();
  await expect(page.getByText(name)).toBeVisible({ timeout: 10_000 });
}

async function createDriver(page: Page, name: string) {
  await page.goto("/motoristas");
  await page.getByRole("button", { name: "Novo motorista" }).click();
  await page.fill("#driver-nome", name);
  await page.fill("#driver-cpf", uniqueDigits(11));
  await page.getByRole("button", { name: "Criar motorista" }).click();
  await expect(page.getByText(name)).toBeVisible({ timeout: 10_000 });
}

async function createVehicle(page: Page, plate: string): Promise<string> {
  await page.goto("/veiculos");
  await page.getByRole("button", { name: "Novo veículo" }).click();
  await page.fill("#vehicle-plate", plate);
  await page.fill("#vehicle-renavam", uniqueDigits(11));
  await page.fill("#vehicle-fabricante", "Volvo");
  await page.fill("#vehicle-modelo", "FH540");
  await page.fill("#vehicle-ano", "2023");
  await page.fill("#vehicle-categoria", CATEGORY_ID);
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/veiculos")),
    page.getByRole("button", { name: "Criar veículo" }).click(),
  ]);
  const vehicle = (await response.json()) as { id: string };
  await expect(page.getByText(plate)).toBeVisible({ timeout: 10_000 });
  return vehicle.id;
}

async function createSupplier(page: Page, name: string): Promise<string> {
  await page.goto("/fornecedores");
  await page.getByRole("button", { name: "Novo fornecedor" }).click();
  await page.fill("#supplier-razao-social", name);
  await page.fill("#supplier-cnpj", uniqueDigits(14));
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/suppliers")),
    page.getByRole("button", { name: "Criar fornecedor" }).click(),
  ]);
  const supplier = (await response.json()) as { id: string };
  await expect(page.getByText(name)).toBeVisible({ timeout: 10_000 });
  return supplier.id;
}

async function createCostCenter(page: Page, name: string): Promise<string> {
  await page.goto("/centros-custo");
  await page.getByRole("button", { name: "Novo centro de custo" }).click();
  await page.fill("#cost-center-nome", name);
  await page.fill("#cost-center-accounting-code", `CC-${uniqueDigits(6)}`);
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/cost-centers")),
    page.getByRole("button", { name: "Criar centro de custo" }).click(),
  ]);
  const costCenter = (await response.json()) as { id: string };
  await expect(page.getByText(name)).toBeVisible({ timeout: 10_000 });
  return costCenter.id;
}

async function createChartOfAccounts(page: Page, name: string): Promise<string> {
  await page.goto("/plano-contas");
  await page.getByRole("button", { name: "Nova conta" }).click();
  await page.fill("#chart-code", `CTA-${uniqueDigits(6)}`);
  await page.fill("#chart-name", name);
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/plano-contas")),
    page.getByRole("dialog").getByRole("button", { name: "Criar conta" }).click(),
  ]);
  const account = (await response.json()) as { id: string };
  // `getByText(name)` também bate no `<option>` espelho oculto do próprio Select "Conta-pai" (Radix
  // sincroniza um `<select>` nativo por trás de cada Select para semântica de formulário) — escopo
  // no botão real da árvore (`ChartOfAccountsTree`'s `TreeRow`) evita a ambiguidade.
  await expect(page.getByRole("button", { name: new RegExp(name) })).toBeVisible({ timeout: 10_000 });
  return account.id;
}

async function createBankAccount(page: Page, bankName: string): Promise<string> {
  await page.goto("/contas-bancarias");
  await page.getByRole("button", { name: "Nova conta bancária" }).click();
  await page.fill("#bank-account-bank", bankName);
  await page.fill("#bank-account-branch", "0001");
  await page.fill("#bank-account-number", uniqueDigits(8));
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/contas-bancarias")),
    page.getByRole("button", { name: "Criar conta bancária" }).click(),
  ]);
  const bankAccount = (await response.json()) as { id: string };
  await expect(page.getByText(bankName)).toBeVisible({ timeout: 10_000 });
  return bankAccount.id;
}

interface WorkOrderFinancials {
  supplierName: string;
  costCenterName: string;
  chartName: string;
}

async function createWorkOrderWithFinancials(
  page: Page, plate: string, description: string, financials: WorkOrderFinancials
): Promise<string> {
  await page.goto("/ordens-servico");
  await page.getByRole("button", { name: "Nova ordem de serviço" }).click();
  await page.getByLabel("Veículo").click();
  await page.getByRole("option", { name: plate }).click();
  await page.fill("#work-order-problem-description", description);
  await page.getByLabel("Fornecedor executor (opcional)").click();
  await page.getByRole("option", { name: financials.supplierName }).click();
  await page.getByLabel("Centro de custo (opcional)").click();
  await page.getByRole("option", { name: financials.costCenterName }).click();
  await page.getByLabel("Plano de contas (opcional)").click();
  await page.getByRole("option", { name: new RegExp(financials.chartName) }).click();

  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/ordens-servico")),
    page.getByRole("button", { name: "Criar ordem de serviço" }).click(),
  ]);
  const workOrder = (await response.json()) as { id: string };
  await expect(page.getByText("Ordem de serviço criada.")).toBeVisible({ timeout: 10_000 });
  await page.goto(`/ordens-servico/${workOrder.id}`);
  return workOrder.id;
}

async function closeWorkOrderWithHighValueItem(page: Page, itemValue: string) {
  await page.getByRole("button", { name: "Diagnosticar" }).click();
  await page.fill("#work-order-technical-diagnosis", "Diagnóstico técnico E2E.");
  await page.getByRole("button", { name: "Salvar diagnóstico" }).click();
  await expect(page.getByText("Diagnóstico registrado.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("button", { name: "Iniciar execução" }).click();
  await expect(page.getByText("Execução iniciada.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("tab", { name: "Itens" }).click();
  await page.getByRole("button", { name: "Novo item" }).click();
  await page.fill("#work-order-item-description", "Peça de alto valor");
  await page.fill("#work-order-item-quantity", "1");
  await page.fill("#work-order-item-unit-value", itemValue);
  await page.getByRole("button", { name: "Adicionar item" }).click();
  await expect(page.getByText("Item adicionado.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("button", { name: "Concluir" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Concluir ordem de serviço" }).click();
  await expect(page.getByText("Ordem de serviço concluída.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("button", { name: "Fechar" }).click();
  await expect(page.getByText("Ordem de serviço fechada.")).toBeVisible({ timeout: 10_000 });
}

async function allocateAndReleaseTrip(page: Page, driverName: string, plate: string) {
  await page.getByRole("tab", { name: "Recursos" }).click();
  await page.getByRole("button", { name: "Alocar recursos" }).click();
  await page.getByLabel("Motorista").click();
  await page.getByRole("option", { name: driverName }).click();
  await page.getByLabel("Veículo tracionador").click();
  await page.getByRole("option", { name: plate }).click();
  await page.getByRole("button", { name: "Salvar" }).click();
  await expect(page.getByText("Recursos alocados.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("tab", { name: "Checklist" }).click();
  await page.getByRole("button", { name: "Novo checklist" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Criar checklist" }).click();
  await expect(page.getByText("Checklist criado.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("button", { name: "Iniciar preenchimento" }).click();
  await page.getByRole("button", { name: "Adicionar item" }).click();
  await page.fill("#checklist-item-0", "Pneus e estepe");
  await page.getByLabel("Resposta").click();
  await page.getByRole("option", { name: "Conforme", exact: true }).click();
  await page.getByRole("button", { name: "Concluir checklist" }).click();
  await expect(page.getByText("Checklist concluído.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("button", { name: "Aprovar" }).click();
  await expect(page.getByText("Checklist aprovado.")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Liberada", { exact: true })).toBeVisible({ timeout: 10_000 });
}

/**
 * `receive_cte_sefaz_response` (`documents/application/fiscal_internal_transitions.py`) — a única
 * transição que leva `Trip.status_fiscal` a `CTE_EMITIDO` — não tem rota HTTP nenhuma (D397,
 * "simula as duas transições genuinamente externas... nenhum método aqui é acionável por HTTP").
 * Não existe caminho real de UI/API para chegar em CT-e Autorizado nesta base — gap herdado da
 * Lote Documentos Fiscais, não desta Lote. Simulação mínima e explícita da resposta SEFAZ, mesmo
 * princípio já usado por `fiscal-seed.sql`/`fiscal.spec.ts` (CT-e Autorizado pré-semeado, nunca
 * alcançado pela UI ali também) — só que aqui incide sobre a Viagem/CT-e criados de verdade pela
 * aplicação neste teste, não uma linha estática.
 */
function simulateSefazAuthorization(tripId: string, cteId: string) {
  const suffix = Date.now();
  const sql = `
    UPDATE ctes SET status = 'AUTORIZADO', protocolo_sefaz = 'SEFAZ-E2E-${suffix}',
      chave_acesso = '${suffix.toString().padStart(44, "0")}', xml_arquivo_id = gen_random_uuid(),
      data_hora_autorizacao = now(), atualizado_em = now()
    WHERE id = '${cteId}';
    UPDATE viagens SET status_fiscal = 'CTE_EMITIDO' WHERE id = '${tripId}';
  `;
  execFileSync("docker", ["exec", "-i", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-v", "ON_ERROR_STOP=1"], {
    input: sql, stdio: ["pipe", "inherit", "inherit"],
  });
}

test.describe("Sprint 15 — Frontend, Lote Financeiro (Parte 2)", () => {
  test("OS fechada gera Conta a Pagar automática → aprovação → pagamento → saldo/status corretos", async ({ page }) => {
    await login(page, "financeiro-admin@e2e-fixture.com");
    const suffix = Date.now();
    const plate = `FN${suffix.toString().slice(-5)}`;
    const supplierName = `Fornecedor Financeiro E2E ${suffix}`;
    const costCenterName = `Centro de Custo Financeiro E2E ${suffix}`;
    const chartName = `Conta Contábil Financeiro E2E ${suffix}`;
    const bankName = `Banco Financeiro E2E ${suffix}`;

    await createVehicle(page, plate);
    await createSupplier(page, supplierName);
    await createCostCenter(page, costCenterName);
    await createChartOfAccounts(page, chartName);
    await createBankAccount(page, bankName);

    const workOrderId = await createWorkOrderWithFinancials(page, plate, "Motor com ruído — peça de alto valor.", {
      supplierName, costCenterName, chartName,
    });
    // Acima da alçada padrão (R$ 1.000,00) — força AGUARDANDO_APROVACAO na Conta a Pagar automática.
    await closeWorkOrderWithHighValueItem(page, "1500.00");

    await page.goto("/contas-pagar");
    await page.getByRole("link", { name: supplierName }).click();
    await page.waitForURL(/\/contas-pagar\/[0-9a-f-]+$/);
    // Aparece tanto no breadcrumb quanto no título — `.first()` só confirma presença, não unicidade.
    await expect(page.getByText("R$ 1.500,00").first()).toBeVisible({ timeout: 10_000 });

    // Rastreabilidade: a Conta a Pagar deixa claro que nasceu da OS, sem lançamento manual.
    await expect(page.getByRole("link", { name: "Ver ordem de serviço" })).toHaveAttribute("href", `/ordens-servico/${workOrderId}`);
    await expect(page.getByText("Nasceu automaticamente no fechamento da Ordem de Serviço")).toBeVisible();

    await page.getByRole("button", { name: "Aprovar" }).click();
    await expect(page.getByText("Conta a pagar aprovada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Aprovada", { exact: true }).first()).toBeVisible();

    await page.getByRole("button", { name: "Pagar" }).click();
    await page.getByLabel("Conta bancária").click();
    await page.getByRole("option", { name: new RegExp(bankName) }).click();
    await page.getByRole("button", { name: "Confirmar pagamento" }).click();
    await expect(page.getByText("Conta a pagar paga.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Paga", { exact: true }).first()).toBeVisible();

    // Saldo derivado: PAGA vira 0, nunca um segundo campo fabricado.
    await page.goto("/contas-pagar");
    const row = page.getByRole("row").filter({ hasText: supplierName });
    await expect(row.getByText("R$ 0,00")).toBeVisible({ timeout: 10_000 });
  });

  test("usuário sem financial.payable.approve não vê o botão e é barrado pelo backend, não só pela UI", async ({ page, request }) => {
    await login(page, "financeiro-admin@e2e-fixture.com");
    const suffix = Date.now();
    const plate = `FL${suffix.toString().slice(-5)}`;
    const supplierName = `Fornecedor Limitado E2E ${suffix}`;
    const costCenterName = `Centro Limitado E2E ${suffix}`;
    const chartName = `Conta Limitada E2E ${suffix}`;

    await createVehicle(page, plate);
    await createSupplier(page, supplierName);
    await createCostCenter(page, costCenterName);
    await createChartOfAccounts(page, chartName);
    const workOrderId = await createWorkOrderWithFinancials(page, plate, "Suspensão — peça de alto valor.", {
      supplierName, costCenterName, chartName,
    });
    await closeWorkOrderWithHighValueItem(page, "2000.00");

    await page.goto("/contas-pagar");
    const [listResponse] = await Promise.all([
      // "/api/v1/contas-pagar", não só "/contas-pagar" — o próprio documento HTML da página do
      // Next.js em `/contas-pagar` também bate no substring mais curto.
      page.waitForResponse((res) => res.request().method() === "GET" && res.url().includes("/api/v1/contas-pagar")),
      page.reload(),
    ]);
    const payables = (await listResponse.json()) as { data: Array<{ id: string; maintenance_order_id: string | null }> };
    const payable = payables.data.find((p) => p.maintenance_order_id === workOrderId);
    if (!payable) throw new Error("Conta a pagar automática não encontrada para a OS de teste.");

    const adminToken = await getAuthToken(request, "financeiro-admin@e2e-fixture.com");

    // Barrado pelo backend mesmo com o ID em mãos e chamando a API diretamente — esconder o botão
    // não é a autorização real.
    const limitedToken = await getAuthToken(request, "financeiro-limitado@e2e-fixture.com");
    const directApprove = await request.post(`${API_BASE_URL}/contas-pagar/${payable.id}/commands/approve`, {
      headers: { Authorization: `Bearer ${limitedToken}` }, data: {},
    });
    expect(directApprove.status()).toBe(403);
    expect((await directApprove.json()).error.code).toBe("IDENTITY_PERMISSION_DENIED");

    // Confirma que o admin (com permissão) continua conseguindo — não é um bloqueio geral quebrado.
    const adminApprove = await request.post(`${API_BASE_URL}/contas-pagar/${payable.id}/commands/approve`, {
      headers: { Authorization: `Bearer ${adminToken}` }, data: {},
    });
    expect(adminApprove.status()).toBe(200);

    // E na UI: o usuário limitado nunca vê o botão "Aprovar", mesmo estando na tela certa.
    await login(page, "financeiro-limitado@e2e-fixture.com");
    await page.goto(`/contas-pagar/${payable.id}`);
    await expect(page.getByRole("button", { name: "Aprovar" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Pagar" })).toHaveCount(0);
  });

  test("Viagem elegível → Fatura → Conta a Receber → baixa parcial → saldo remanescente → baixa final", async ({ page, request }) => {
    await login(page, "financeiro-admin@e2e-fixture.com");
    const suffix = Date.now();
    const clientName = `Cliente Financeiro E2E ${suffix}`;
    const driverName = `Motorista Financeiro E2E ${suffix}`;
    const plate = `FR${suffix.toString().slice(-5)}`;

    await createClient(page, clientName);
    await createDriver(page, driverName);
    await createVehicle(page, plate);

    await page.goto("/viagens");
    await page.getByRole("button", { name: "Nova viagem" }).click();
    await page.getByLabel("Cliente").click();
    await page.getByRole("option", { name: clientName }).click();
    const [tripResponse] = await Promise.all([
      page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/viagens")),
      page.getByRole("button", { name: "Criar viagem" }).click(),
    ]);
    const trip = (await tripResponse.json()) as { id: string };
    await expect(page.getByText("Viagem criada.")).toBeVisible({ timeout: 10_000 });
    await page.goto(`/viagens/${trip.id}`);

    await allocateAndReleaseTrip(page, driverName, plate);

    // Não existe `POST /ctes` (D396) — o CT-e nasce como efeito colateral de
    // `POST /viagens/{id}/commands/dispatch`, que devolve a própria Viagem, não o CT-e criado.
    // Busca-se o CT-e recém-criado por `trip_id` depois, via API direta (mesmo motivo de
    // `getAuthToken` no teste de permissão — o `request` fixture não tem a sessão do `page`).
    await Promise.all([
      page.waitForResponse((res) => res.request().method() === "POST" && res.url().includes("/commands/dispatch")),
      page.getByRole("button", { name: "Despachar" }).click(),
    ]);
    await expect(page.getByText("Viagem despachada.")).toBeVisible({ timeout: 10_000 });

    const adminToken = await getAuthToken(request, "financeiro-admin@e2e-fixture.com");
    const ctesResponse = await request.get(`${API_BASE_URL}/ctes?trip_id=${trip.id}`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    const ctes = (await ctesResponse.json()) as { data: Array<{ id: string }> };
    const cte = ctes.data[0];
    if (!cte) throw new Error("CT-e não foi criado no despacho da viagem de teste.");

    // Entrega + Canhoto — via UI real, precondição de Faturamento.
    await page.getByRole("tab", { name: "Entregas" }).click();
    await page.getByRole("button", { name: "Nova entrega" }).click();
    await page.fill("#delivery-order", "1");
    await page.fill("#delivery-recipient", "Destinatário E2E Financeiro");
    await page.fill("#delivery-logradouro", "Av. Financeiro");
    await page.fill("#delivery-cidade", "São Paulo");
    await page.fill("#delivery-uf", "SP");
    await page.fill("#delivery-cep", "01000-000");
    await page.getByRole("button", { name: "Criar entrega" }).click();
    await expect(page.getByText("Entrega criada.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Editar" }).click();
    const editDialog = page.getByRole("dialog");
    await editDialog.getByLabel("Status").click();
    await page.getByRole("option", { name: "Concluída" }).click();
    await editDialog.getByRole("button", { name: "Salvar" }).click();
    await expect(page.getByText("Entrega atualizada.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Registrar canhoto" }).click();
    await expect(page.getByText("Canhoto registrado.")).toBeVisible({ timeout: 10_000 });

    // CT-e Autorizado — sem caminho de UI/API real nesta base (ver `simulateSefazAuthorization`).
    simulateSefazAuthorization(trip.id, cte.id);

    await page.goto("/faturas");
    await page.getByRole("button", { name: "Nova fatura" }).click();
    await page.getByLabel("Cliente").click();
    await page.getByRole("option", { name: clientName }).click();
    await page.getByLabel("Viagem").click();
    await page.getByRole("option", { name: new RegExp("^VG-") }).click();
    await page.fill("#invoice-payment-method", PAYMENT_METHOD_ID);
    await page.fill("#installment-value-0", "600");
    await page.fill("#installment-due-0", "2026-12-01");
    await page.fill("#installment-competencia-0", "2026-12-01");
    await page.getByRole("button", { name: "Adicionar parcela" }).click();
    await page.fill("#installment-value-1", "400");
    await page.fill("#installment-due-1", "2026-12-15");
    await page.fill("#installment-competencia-1", "2026-12-01");

    const [invoiceResponse] = await Promise.all([
      page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/faturas")),
      page.getByRole("button", { name: "Criar fatura" }).click(),
    ]);
    await expect(page.getByText("Fatura criada.")).toBeVisible({ timeout: 10_000 });
    const invoice = (await invoiceResponse.json()) as { id: string };
    await page.goto(`/faturas/${invoice.id}`);

    // Aparece em breadcrumb + "Valor total" + resumo "Faturado"/"Saldo" (saldo == total antes de
    // qualquer baixa) — `.first()` só confirma presença, não unicidade.
    await expect(page.getByText("R$ 1.000,00").first()).toBeVisible({ timeout: 10_000 });

    // Baixa parcial: confirma só a primeira parcela — saldo remanescente visível e correto.
    const rows = page.getByRole("row");
    await rows.filter({ hasText: "R$ 600,00" }).getByRole("button", { name: "Confirmar recebimento" }).click();
    await expect(page.getByText("Recebimento confirmado.")).toBeVisible({ timeout: 10_000 });
    // "R$ 400,00" aparece tanto no card de Saldo quanto na célula Valor da parcela 2 pendente —
    // a segunda é prova suficiente de saldo remanescente correto, sem ambiguidade de locator.
    await expect(rows.filter({ hasText: "R$ 400,00" })).toBeVisible({ timeout: 10_000 });

    // Baixa final: confirma a segunda parcela — saldo some, Fatura 100% recebida.
    await rows.filter({ hasText: "R$ 400,00" }).getByRole("button", { name: "Confirmar recebimento" }).click();
    await expect(page.getByText("Recebimento confirmado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("R$ 0,00")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: "Confirmar recebimento" })).toHaveCount(0);
  });
});
