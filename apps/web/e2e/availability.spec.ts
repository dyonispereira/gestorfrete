import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";

async function login(page: Page) {
  await page.goto("/login");
  await page.fill("#email", "availability-admin@e2e-fixture.com");
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
  await page.getByLabel("Categoria").click();
  await page.getByRole("option", { name: "E2E Categoria" }).click();

  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/veiculos")),
    page.getByRole("button", { name: "Criar veículo" }).click(),
  ]);
  const vehicle = (await response.json()) as { id: string };
  await expect(page.getByText(plate)).toBeVisible({ timeout: 10_000 });
  return vehicle.id;
}

async function createTrip(page: Page, clientName: string): Promise<string> {
  await page.goto("/viagens");
  await page.getByRole("button", { name: "Nova viagem" }).click();
  await page.getByLabel("Cliente").click();
  await page.getByRole("option", { name: clientName }).click();

  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/viagens")),
    page.getByRole("button", { name: "Criar viagem" }).click(),
  ]);
  const trip = (await response.json()) as { id: string };
  await expect(page.getByText("Viagem criada.")).toBeVisible({ timeout: 10_000 });
  await page.goto(`/viagens/${trip.id}`);
  return trip.id;
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

async function dispatchTrip(page: Page) {
  await page.getByRole("button", { name: "Despachar" }).click();
  await expect(page.getByText("Viagem despachada.")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Em deslocamento", { exact: true })).toBeVisible();
}

async function closeAdministratively(page: Page) {
  await page.getByRole("button", { name: "Encerramento administrativo" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.locator("#command-text").fill("Encerramento administrativo de teste E2E.");
  await dialog.getByRole("button", { name: "Encerrar administrativamente" }).click();
  await expect(page.getByText("Viagem atualizada.")).toBeVisible({ timeout: 10_000 });
}

async function availabilityRowStatus(page: Page, vehicleId: string) {
  await page.goto("/disponibilidade");
  const row = page.getByRole("row").filter({ has: page.getByRole("link", { name: vehicleId }) });
  await expect(row).toBeVisible({ timeout: 10_000 });
  return row;
}

async function createWorkOrder(page: Page, plate: string, description: string): Promise<string> {
  await page.goto("/ordens-servico");
  await page.getByRole("button", { name: "Nova ordem de serviço" }).click();
  await page.getByLabel("Veículo").click();
  await page.getByRole("option", { name: plate }).click();
  await page.fill("#work-order-problem-description", description);

  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/ordens-servico")),
    page.getByRole("button", { name: "Criar ordem de serviço" }).click(),
  ]);
  const workOrder = (await response.json()) as { id: string };
  await expect(page.getByText("Ordem de serviço criada.")).toBeVisible({ timeout: 10_000 });
  await page.goto(`/ordens-servico/${workOrder.id}`);
  return workOrder.id;
}

async function concludeWorkOrder(page: Page) {
  await page.getByRole("button", { name: "Diagnosticar" }).click();
  await page.fill("#work-order-technical-diagnosis", "Diagnóstico técnico E2E.");
  await page.getByRole("button", { name: "Salvar diagnóstico" }).click();
  await expect(page.getByText("Diagnóstico registrado.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("button", { name: "Iniciar execução" }).click();
  await expect(page.getByText("Execução iniciada.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("tab", { name: "Itens" }).click();
  await page.getByRole("button", { name: "Novo item" }).click();
  await page.fill("#work-order-item-description", "Reparo rápido");
  await page.fill("#work-order-item-quantity", "1");
  await page.fill("#work-order-item-unit-value", "100");
  await page.getByRole("button", { name: "Adicionar item" }).click();
  await expect(page.getByText("Item adicionado.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("button", { name: "Concluir" }).click();
  const concludeDialog = page.getByRole("dialog");
  await concludeDialog.getByRole("button", { name: "Concluir ordem de serviço" }).click();
  await expect(page.getByText("Ordem de serviço concluída.")).toBeVisible({ timeout: 10_000 });
}

/**
 * Sprint 15 — Lote Frota e Manutenção, Parte 3 (Availability Hardening). `disponibilidade_veiculo`
 * deixou de ser um status sobrescrito pelo último evento — agora é uma projeção de impedimentos
 * ativos (`veiculo_impedimentos`). Prova os dois pontos pedidos: o lado `freight` do projetor, que
 * faltava (`apply_trip_dispatched`/`apply_trip_ended`), e a correção do gap de impedimentos
 * concorrentes (Viagem + OS no mesmo veículo — encerrar só um nunca libera indevidamente).
 */
test.describe("Sprint 15 — Frontend, Lote Frota e Manutenção (Availability Hardening)", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("ciclo de vida: sem impedimento → despacho → Em viagem → encerramento → Disponível", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Disponibilidade E2E ${suffix}`;
    const driverName = `Motorista Disponibilidade E2E ${suffix}`;
    const plate = `DV${suffix.toString().slice(-5)}`;

    await createClient(page, clientName);
    await createDriver(page, driverName);
    const vehicleId = await createVehicle(page, plate);
    const tripId = await createTrip(page, clientName);
    await allocateAndReleaseTrip(page, driverName, plate);

    // Antes do despacho: nenhum impedimento — o veículo nem aparece na projeção.
    await page.goto("/disponibilidade");
    await expect(page.getByRole("link", { name: vehicleId })).toHaveCount(0);

    await page.goto(`/viagens/${tripId}`);
    await dispatchTrip(page);

    const rowAfterDispatch = await availabilityRowStatus(page, vehicleId);
    await expect(rowAfterDispatch.getByText("Em viagem", { exact: true })).toBeVisible();

    await page.goto(`/viagens/${tripId}`);
    await closeAdministratively(page);

    const rowAfterClose = await availabilityRowStatus(page, vehicleId);
    await expect(rowAfterClose.getByText("Disponível", { exact: true })).toBeVisible();
  });

  test("conflito: Viagem + OS no mesmo veículo — encerrar só um não libera indevidamente", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Conflito E2E ${suffix}`;
    const driverName = `Motorista Conflito E2E ${suffix}`;
    const plate = `CF${suffix.toString().slice(-5)}`;

    await createClient(page, clientName);
    await createDriver(page, driverName);
    const vehicleId = await createVehicle(page, plate);
    const tripId = await createTrip(page, clientName);
    await allocateAndReleaseTrip(page, driverName, plate);
    await dispatchTrip(page);

    let row = await availabilityRowStatus(page, vehicleId);
    await expect(row.getByText("Em viagem", { exact: true })).toBeVisible();

    // Segundo impedimento no mesmo veículo — MANUTENCAO tem prioridade de exibição sobre VIAGEM.
    await createWorkOrder(page, plate, "Pane detectada durante a viagem.");
    row = await availabilityRowStatus(page, vehicleId);
    await expect(row.getByText("Em manutenção", { exact: true })).toBeVisible();

    // Encerra só a OS — a Viagem segue ativa, o veículo NUNCA deve voltar a Disponível aqui.
    await page.goBack();
    await concludeWorkOrder(page);
    row = await availabilityRowStatus(page, vehicleId);
    await expect(row.getByText("Em viagem", { exact: true })).toBeVisible();
    await expect(row.getByText("Disponível", { exact: true })).toHaveCount(0);

    // Só depois de encerrar o segundo impedimento (a Viagem) o veículo libera de verdade.
    await page.goto(`/viagens/${tripId}`);
    await closeAdministratively(page);
    row = await availabilityRowStatus(page, vehicleId);
    await expect(row.getByText("Disponível", { exact: true })).toBeVisible();
  });
});
