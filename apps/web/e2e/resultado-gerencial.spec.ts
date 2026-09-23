import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";
const CATEGORY_ID = "f14a0000-0000-0000-0000-0000000000c2";
const ADMIN_EMAIL = "resultado-admin@e2e-fixture.com";
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

async function createClient(page: Page, name: string): Promise<string> {
  await page.goto("/clientes");
  await page.getByRole("button", { name: "Novo cliente" }).click();
  await page.fill("#client-razao-social", name);
  await page.fill("#client-document", uniqueDigits(14));
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/clients")),
    page.getByRole("button", { name: "Criar cliente" }).click(),
  ]);
  const client = (await response.json()) as { id: string };
  await expect(page.getByText(name)).toBeVisible({ timeout: 10_000 });
  return client.id;
}

async function createDriver(page: Page, name: string): Promise<string> {
  await page.goto("/motoristas");
  await page.getByRole("button", { name: "Novo motorista" }).click();
  await page.fill("#driver-nome", name);
  await page.fill("#driver-cpf", uniqueDigits(11));
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/drivers")),
    page.getByRole("button", { name: "Criar motorista" }).click(),
  ]);
  const driver = (await response.json()) as { id: string };
  await expect(page.getByText(name)).toBeVisible({ timeout: 10_000 });
  return driver.id;
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
  await expect(page.getByRole("button", { name: new RegExp(name) })).toBeVisible({ timeout: 10_000 });
  return account.id;
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

async function createFullyInvoiceableTrip(
  page: Page, request: APIRequestContext, clientName: string, driverName: string, plate: string,
  departureOdometerKm?: string,
): Promise<{ tripId: string; codigo: string }> {
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

  // V1 Operational Hardening, Parte 2 — hodômetro de saída (opcional), campo inline ao lado do
  // botão "Despachar" (nunca atrás de um diálogo extra — single click continua válido sem ele).
  if (departureOdometerKm) {
    await page.fill("#trip-departure-odometer-km", departureOdometerKm);
  }
  await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().includes("/commands/dispatch")),
    page.getByRole("button", { name: "Despachar" }).click(),
  ]);
  await expect(page.getByText("Viagem despachada.")).toBeVisible({ timeout: 10_000 });

  const adminToken = await getAuthToken(request, ADMIN_EMAIL);
  const tripDetailResponse = await request.get(`${API_BASE_URL}/viagens/${trip.id}`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  const codigo = (await tripDetailResponse.json()).codigo as string;

  const ctesResponse = await request.get(`${API_BASE_URL}/ctes?trip_id=${trip.id}`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  const ctes = (await ctesResponse.json()) as { data: Array<{ id: string }> };
  const cte = ctes.data[0];
  if (!cte) throw new Error("CT-e não foi criado no despacho da viagem de teste.");

  await page.getByRole("tab", { name: "Entregas" }).click();
  await page.getByRole("button", { name: "Nova entrega" }).click();
  await page.fill("#delivery-order", "1");
  await page.fill("#delivery-recipient", "Destinatário E2E Resultado Gerencial");
  await page.fill("#delivery-logradouro", "Av. Resultado");
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

  await page.goto(`/ctes/${cte.id}`);
  await page.getByRole("button", { name: "Validar" }).click();
  await expect(page.getByText("CT-e validado.")).toBeVisible({ timeout: 10_000 });
  await page.getByRole("button", { name: "Assinar" }).click();
  await expect(page.getByText("CT-e assinado.")).toBeVisible({ timeout: 10_000 });
  await page.getByRole("button", { name: "Transmitir" }).click();
  await expect(page.getByText("CT-e transmitido à SEFAZ.")).toBeVisible({ timeout: 10_000 });
  await page.getByRole("button", { name: "Simular resposta SEFAZ" }).click();
  await expect(page.getByText("Resposta da SEFAZ recebida (simulada).")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Autorizado", { exact: true })).toBeVisible({ timeout: 10_000 });

  return { tripId: trip.id, codigo };
}

async function createPayable(
  page: Page,
  opts: {
    origin: "VIAGEM" | "ORDEM_SERVICO" | "AJUSTE_MANUAL";
    supplierName: string;
    costCenterName: string;
    chartName: string;
    value: string;
    tripCodigo?: string;
    workOrderCodigo?: string;
    driverName?: string;
  }
) {
  await page.goto("/contas-pagar");
  await page.getByRole("button", { name: "Nova conta a pagar" }).click();
  await page.getByLabel("Fornecedor").click();
  await page.getByRole("option", { name: opts.supplierName }).click();
  await page.getByLabel("Centro de custo").click();
  await page.getByRole("option", { name: opts.costCenterName }).click();
  await page.getByLabel("Plano de contas").click();
  await page.getByRole("option", { name: new RegExp(opts.chartName) }).click();
  await page.getByLabel("Origem").click();
  const originLabel = { VIAGEM: "Viagem", ORDEM_SERVICO: "Ordem de Serviço", AJUSTE_MANUAL: "Ajuste manual" }[
    opts.origin
  ];
  await page.getByRole("option", { name: originLabel, exact: true }).click();

  if (opts.origin === "VIAGEM" && opts.tripCodigo) {
    await page.getByLabel("Viagem").click();
    await page.getByRole("option", { name: opts.tripCodigo }).click();
  }
  if (opts.origin === "ORDEM_SERVICO" && opts.workOrderCodigo) {
    await page.getByLabel("Ordem de Serviço").click();
    await page.getByRole("option", { name: opts.workOrderCodigo }).click();
  }
  if (opts.driverName) {
    await page.getByLabel("Motorista (opcional").click();
    await page.getByRole("option", { name: opts.driverName }).click();
  }

  await page.fill("#payable-value", opts.value);
  await page.fill("#payable-due-date", "2026-12-01");
  await page.fill("#payable-competencia", "2026-11-01");
  await page.getByRole("button", { name: "Criar conta a pagar" }).click();
  await expect(page.getByText("Conta a pagar criada.")).toBeVisible({ timeout: 10_000 });
}

async function createWorkOrder(page: Page, plate: string): Promise<string> {
  await page.goto("/ordens-servico");
  await page.getByRole("button", { name: "Nova ordem de serviço" }).click();
  await page.getByLabel("Veículo").click();
  await page.getByRole("option", { name: plate }).click();
  await page.fill("#work-order-problem-description", "Vazamento de óleo no motor.");
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/ordens-servico")),
    page.getByRole("button", { name: "Criar ordem de serviço" }).click(),
  ]);
  const workOrder = (await response.json()) as { id: string; codigo: string };
  await expect(page.getByText("Ordem de serviço criada.")).toBeVisible({ timeout: 10_000 });
  return workOrder.codigo;
}

test.describe("Sprint — Resultado Gerencial (Lote 4)", () => {
  test.setTimeout(240_000);

  test("2 clientes + 2 veículos + 2 motoristas + Fatura agrupada + OS fora de viagem — resultado nunca dobra nem vaza entre dimensões", async ({
    page,
    request,
  }) => {
    await login(page, ADMIN_EMAIL);
    const suffix = Date.now();
    const clientAName = `Cliente Resultado A E2E ${suffix}`;
    const clientBName = `Cliente Resultado B E2E ${suffix}`;
    const driver1Name = `Motorista Resultado 1 E2E ${suffix}`;
    const driver2Name = `Motorista Resultado 2 E2E ${suffix}`;
    const plateV1 = `RA${suffix.toString().slice(-5)}`;
    const plateV2 = `RB${suffix.toString().slice(-5)}`;
    const supplierName = `Oficina Resultado E2E ${suffix}`;
    const costCenterName = `Frota Resultado E2E ${suffix}`;
    const chartName = `Manutenção Resultado E2E ${suffix}`;

    await createClient(page, clientAName);
    await createClient(page, clientBName);
    await createDriver(page, driver1Name);
    await createDriver(page, driver2Name);
    await createVehicle(page, plateV1);
    await createVehicle(page, plateV2);
    await createSupplier(page, supplierName);
    await createCostCenter(page, costCenterName);
    await createChartOfAccounts(page, chartName);

    // Duas Viagens do mesmo Cliente A — vão para 1 Fatura agrupada. Veículo/Motorista DIFERENTES
    // em cada uma (V1/Motorista 1 na tripA, V2/Motorista 2 na tripB): uma Viagem só pode alocar um
    // Veículo que não esteja "vigente" em outra Viagem ao mesmo tempo (D188) — reusar o mesmo
    // Veículo nas duas exigiria encerrar a primeira Viagem antes, fora do escopo deste teste. Isso
    // ainda prova tudo que o usuário pediu: Fatura agrupada de um Cliente com Viagens de
    // Veículos/Motoristas diferentes, e cada dimensão soma exatamente as Viagens que lhe cabem.
    const tripA = await createFullyInvoiceableTrip(page, request, clientAName, driver1Name, plateV1, "100000.00");
    const tripB = await createFullyInvoiceableTrip(page, request, clientAName, driver2Name, plateV2);

    // Fatura agrupada: tripA (600) + tripB (400) = 1000. Baixa parcial (300) + baixa final (700) —
    // "recebimentos parciais" pedido explicitamente pelo usuário.
    await page.goto("/faturas/nova");
    await page.getByLabel("Cliente").click();
    await page.getByRole("option", { name: clientAName }).click();
    const rowA = page.getByRole("row").filter({ hasText: tripA.codigo });
    const rowB = page.getByRole("row").filter({ hasText: tripB.codigo });
    await expect(rowA).toBeVisible({ timeout: 10_000 });
    await expect(rowB).toBeVisible({ timeout: 10_000 });
    await rowA.getByRole("checkbox").click();
    await rowA.locator('input[type="number"]').fill("600");
    await rowB.getByRole("checkbox").click();
    await rowB.locator('input[type="number"]').fill("400");
    await page.getByLabel("Forma de pagamento").click();
    await page.getByRole("option", { name: "PIX" }).click();
    await page.fill("#new-invoice-installment-value-0", "1000");
    await page.fill("#new-invoice-installment-due-0", "2026-12-01");
    await page.fill("#new-invoice-installment-competencia-0", "2026-12-01");
    await page.getByRole("button", { name: "Gerar Fatura" }).click();
    await expect(page.getByText("Fatura criada.")).toBeVisible({ timeout: 10_000 });
    await page.waitForURL(/\/faturas\/[0-9a-f-]+$/);
    const invoiceAB = page.url();

    await page.getByRole("tab", { name: "Financeiro" }).click();
    await page.getByRole("button", { name: "Confirmar recebimento" }).click();
    const paymentDialog = page.getByRole("dialog");
    await paymentDialog.getByLabel("Valor recebido").fill("300");
    await paymentDialog.getByRole("button", { name: "Confirmar recebimento" }).click();
    await expect(page.getByText("Recebimento confirmado.").first()).toBeVisible({ timeout: 10_000 });

    await page.goto(invoiceAB);
    await page.getByRole("tab", { name: "Financeiro" }).click();
    await page.getByRole("button", { name: "Confirmar recebimento" }).click();
    await paymentDialog.getByRole("button", { name: "Confirmar recebimento" }).click();
    await expect(page.getByText("Recebimento confirmado.").first()).toBeVisible({ timeout: 10_000 });
    // tripA.receita_realizada = 600 (600/1000 × 1000 recebido), tripB.receita_realizada = 400.

    // CP de Viagem: 50, contra tripA — bump em tripA.custo_realizado, nunca em tripB.
    await createPayable(page, {
      origin: "VIAGEM", supplierName, costCenterName, chartName, value: "50.00", tripCodigo: tripA.codigo,
    });

    // OS fora de Viagem, no Veículo V1 (o mesmo de tripA/tripB) — nunca referencia uma Viagem.
    const workOrderCodigo = await createWorkOrder(page, plateV1);
    // CP de Manutenção: 1200, contra a OS — sobe o custo do Veículo V1, nunca o de uma Viagem/Motorista.
    await createPayable(page, {
      origin: "ORDEM_SERVICO", supplierName, costCenterName, chartName, value: "1200.00", workOrderCodigo,
    });
    // CP vinculada explicitamente ao Motorista 1 — nunca ao Veículo.
    await createPayable(page, {
      origin: "AJUSTE_MANUAL", supplierName, costCenterName, chartName, value: "80.00", driverName: driver1Name,
    });

    // --- Dimensão Viagem: tripA carrega o custo de 50 (a CP de Viagem); tripB não carrega nada
    // extra (nem a CP de Viagem da irmã, nem a Manutenção/custo vinculado do Veículo/Motorista dela).
    await page.goto("/resultados");
    await page.getByRole("tab", { name: "Viagens" }).click();
    const tripARow = page.getByRole("row").filter({ hasText: tripA.codigo });
    const tripBRow = page.getByRole("row").filter({ hasText: tripB.codigo });
    await expect(tripARow).toBeVisible({ timeout: 10_000 });
    await expect(tripARow.getByText("R$ 600,00")).toBeVisible();
    await expect(tripARow.getByText("R$ 50,00")).toBeVisible();
    await expect(tripARow.getByText("R$ 550,00")).toBeVisible(); // margem = 600 - 50
    await expect(tripBRow.getByText("R$ 400,00").first()).toBeVisible();
    await expect(tripBRow.getByText("R$ 0,00")).toBeVisible(); // sem CP própria — margem = receita cheia

    // V1 Operational Hardening, Parte 2/3 — tripA teve o hodômetro de SAÍDA capturado no despacho,
    // mas `commands/finish` é inalcançável pela UI real hoje (sem endpoint de Coleta/Romaneio para
    // avançar até EM_ENTREGA — gap registrado, fora do escopo desta Parte). Com só uma das duas
    // leituras de fronteira, o KM tem que continuar "Indisponível" — nunca uma estimativa a partir
    // de uma leitura só.
    await expect(tripARow.getByText("Indisponível").first()).toBeVisible();

    // --- Dimensão Veículo: V1 (o de tripA) carrega Manutenção (1200) além do custo da própria
    // Viagem (50) — isso NUNCA aparece na Viagem nem no Motorista. V2 (o de tripB) fica intocado.
    await page.goto("/resultados");
    await page.getByRole("tab", { name: "Veículos" }).click();
    const vehicleV1Row = page.getByRole("row").filter({ hasText: plateV1 });
    const vehicleV2Row = page.getByRole("row").filter({ hasText: plateV2 });
    await expect(vehicleV1Row).toBeVisible({ timeout: 10_000 });
    await expect(vehicleV1Row.getByText("R$ 600,00").first()).toBeVisible(); // Receita — só tripA
    await expect(vehicleV1Row.getByText("R$ 50,00")).toBeVisible(); // Custo Viagens
    await expect(vehicleV1Row.getByText("R$ 1.200,00")).toBeVisible(); // Manutenção
    await expect(vehicleV1Row.getByText("R$ 1.250,00")).toBeVisible(); // Custo Total = 50 + 1200
    await expect(vehicleV1Row.getByText("-R$ 650,00")).toBeVisible(); // Resultado = 600 - 1250 < 0
    await expect(vehicleV2Row.getByText("R$ 400,00").first()).toBeVisible(); // tripB sozinha, sem Manutenção

    await vehicleV1Row.getByRole("link").first().click();
    await expect(page.getByRole("heading", { name: "Resultado Operacional de Viagens" })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("R$ 550,00").first()).toBeVisible(); // 600 - 50, sem Manutenção
    const detailTripARow = page.getByRole("row").filter({ hasText: tripA.codigo });
    await expect(detailTripARow.getByText("R$ 550,00")).toBeVisible(); // margem de tripA, idêntica à aba Viagens
    const maintenanceOriginLink = page.getByRole("link", { name: "Manutenção (OS)" });
    await expect(maintenanceOriginLink).toBeVisible();
    await expect(maintenanceOriginLink).toHaveAttribute("href", expect.stringContaining("/ordens-servico/"));
    await expect(page.getByText("R$ 1.200,00").first()).toBeVisible();

    // --- Dimensão Motorista: Motorista 1 carrega 50 (Viagens) + 80 (vinculado) = 130 — nunca os
    // 1200 de Manutenção do Veículo que ele dirigiu. Motorista 2 fica intocado.
    await page.goto("/resultados");
    await page.getByRole("tab", { name: "Motoristas" }).click();
    const driver1Row = page.getByRole("row").filter({ hasText: driver1Name });
    const driver2Row = page.getByRole("row").filter({ hasText: driver2Name });
    await expect(driver1Row).toBeVisible({ timeout: 10_000 });
    await expect(driver1Row.getByText("R$ 600,00").first()).toBeVisible(); // Receita — só tripA
    await expect(driver1Row.getByText("R$ 50,00")).toBeVisible(); // Custo Viagens
    await expect(driver1Row.getByText("R$ 80,00")).toBeVisible(); // Custo Vinculado
    await expect(driver1Row.getByText("R$ 470,00")).toBeVisible(); // Margem = 600 - 130
    await expect(driver2Row.getByText("R$ 400,00").first()).toBeVisible(); // tripB sozinha, sem custo extra

    await driver1Row.getByRole("link").click();
    const driverDetailTripARow = page.getByRole("row").filter({ hasText: tripA.codigo });
    await expect(driverDetailTripARow.getByText("R$ 550,00")).toBeVisible(); // idêntica, nunca alterada pela OS

    // --- Dimensão Cliente: Cliente A soma as duas Viagens (Veículos/Motoristas diferentes); Custo
    // nunca inclui a Manutenção do Veículo que serviu uma delas.
    await page.goto("/resultados");
    await page.getByRole("tab", { name: "Clientes" }).click();
    const clientARow = page.getByRole("row").filter({ hasText: clientAName });
    await expect(clientARow).toBeVisible({ timeout: 10_000 });
    await expect(clientARow.getByText("R$ 1.000,00").first()).toBeVisible(); // Receita Realizada = 600+400
    await expect(clientARow.getByText("R$ 50,00")).toBeVisible(); // Custo — só Viagens (50+0), nunca 1250

    await clientARow.getByRole("link").click();
    await expect(page.getByRole("link", { name: /^FAT-/ }).first()).toBeVisible({ timeout: 10_000 });
    const clientDetailTripARow = page.getByRole("row").filter({ hasText: tripA.codigo });
    await expect(clientDetailTripARow.getByText("R$ 550,00")).toBeVisible();
    // Σ receita das Viagens = receita total considerada: 600 (V1/Motorista 1) + 400 (V2/Motorista 2)
    // = 1000 = Receita Realizada do Cliente A — a mesma soma, atravessando Viagem/Veículo/Motorista/
    // Cliente, nunca duplicada, nunca perdida.
  });
});
