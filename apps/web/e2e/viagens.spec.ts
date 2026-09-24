import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";

async function login(page: Page) {
  await page.goto("/login");
  await page.fill("#email", "viagens-admin@e2e-fixture.com");
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

async function createVehicle(page: Page, plate: string) {
  await page.goto("/veiculos");
  await page.getByRole("button", { name: "Novo veículo" }).click();
  await page.fill("#vehicle-plate", plate);
  await page.fill("#vehicle-renavam", uniqueDigits(11));
  await page.fill("#vehicle-fabricante", "Volvo");
  await page.fill("#vehicle-modelo", "FH540");
  await page.fill("#vehicle-ano", "2023");
  await page.getByLabel("Categoria").click();
  await page.getByRole("option", { name: "E2E Categoria" }).click();
  await page.getByRole("button", { name: "Criar veículo" }).click();
  await expect(page.getByText(plate)).toBeVisible({ timeout: 10_000 });
}

/**
 * Cria a viagem a partir de `/viagens` e navega até o detalhe. O drawer de criação só fecha (não
 * navega, D-nenhum: não existe redirecionamento automático) e `codigo` é gerado pelo Backend
 * (`VG-{ano}-{hex6}`), então não dá para localizar a linha nova na lista por texto previsível —
 * captura o `id` direto da resposta do `POST /viagens` e navega para o detalhe.
 */
async function createTrip(page: Page, clientName: string) {
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
}

async function allocateResources(page: Page, driverName: string, plate: string) {
  await page.getByRole("tab", { name: "Recursos" }).click();
  await page.getByRole("button", { name: "Alocar recursos" }).click();
  await page.getByLabel("Motorista").click();
  await page.getByRole("option", { name: driverName }).click();
  await page.getByLabel("Veículo tracionador").click();
  await page.getByRole("option", { name: plate }).click();
  await page.getByRole("button", { name: "Salvar" }).click();
  await expect(page.getByText("Recursos alocados.")).toBeVisible({ timeout: 10_000 });
}

test.describe("Sprint 13 — Frontend, Lote Operação", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("golden path: criar Viagem, alocar recursos, aceitar", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Viagem E2E ${suffix}`;
    const driverName = `Motorista Viagem E2E ${suffix}`;
    const plate = `VG${suffix.toString().slice(-5)}`;

    await createClient(page, clientName);
    await createDriver(page, driverName);
    await createVehicle(page, plate);
    await createTrip(page, clientName);

    await expect(page.getByText("Rascunho", { exact: true })).toBeVisible();

    await allocateResources(page, driverName, plate);
    await expect(page.getByText("Planejada", { exact: true })).toBeVisible({ timeout: 10_000 });

    await page.getByRole("tab", { name: "Visão Geral" }).click();
    await page.getByRole("button", { name: "Aceitar" }).click();
    await expect(page.getByText("Viagem aceita.")).toBeVisible({ timeout: 10_000 });
  });

  test("Recursos: reatribuir encerra a alocação anterior automaticamente (D188)", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Realoc E2E ${suffix}`;
    const driver1 = `Motorista Realoc A E2E ${suffix}`;
    const driver2 = `Motorista Realoc B E2E ${suffix}`;
    const plate1 = `RA${suffix.toString().slice(-5)}`;
    const plate2 = `RB${suffix.toString().slice(-5)}`;

    await createClient(page, clientName);
    await createDriver(page, driver1);
    await createDriver(page, driver2);
    await createVehicle(page, plate1);
    await createVehicle(page, plate2);
    await createTrip(page, clientName);
    await allocateResources(page, driver1, plate1);

    await page.getByRole("button", { name: "Reatribuir" }).click();
    await page.getByLabel("Motorista").click();
    await page.getByRole("option", { name: driver2 }).click();
    await page.getByLabel("Veículo tracionador").click();
    await page.getByRole("option", { name: plate2 }).click();
    await page.fill("#reallocate-reason", "Motorista original ficou indisponível.");
    await page.getByRole("button", { name: "Salvar" }).click();
    await expect(page.getByText("Recursos realocados")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Ver histórico de alocações" }).click();
    await expect(page.getByText("Substituída", { exact: true })).toHaveCount(1);
  });

  test("Entregas: Recusada exige motivo, e Canhoto some após registrado", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Entrega E2E ${suffix}`;
    await createClient(page, clientName);
    await createTrip(page, clientName);

    await page.getByRole("tab", { name: "Entregas" }).click();
    await page.getByRole("button", { name: "Nova entrega" }).click();
    await page.fill("#delivery-order", "1");
    await page.fill("#delivery-recipient", "Destinatário E2E");
    await page.fill("#delivery-logradouro", "Av. Teste");
    await page.fill("#delivery-cidade", "São Paulo");
    await page.fill("#delivery-uf", "SP");
    await page.fill("#delivery-cep", "01000-000");
    await page.getByRole("button", { name: "Criar entrega" }).click();
    await expect(page.getByText("Entrega criada.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Editar" }).click();
    const editDialog = page.getByRole("dialog");
    await editDialog.getByLabel("Status").click();
    await page.getByRole("option", { name: "Recusada" }).click();
    await editDialog.getByRole("button", { name: "Salvar" }).click();
    await expect(page.getByText("Motivo da recusa é obrigatório")).toBeVisible();

    await editDialog.getByLabel("Status").click();
    await page.getByRole("option", { name: "Concluída" }).click();
    await editDialog.getByRole("button", { name: "Salvar" }).click();
    await expect(page.getByText("Entrega atualizada.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Registrar canhoto" }).click();
    await expect(page.getByText("Canhoto registrado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: "Registrar canhoto" })).toHaveCount(0);
  });

  test("Ocorrências: sem excluir — correção é sempre por status (RESOLVIDA)", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Ocorrencia E2E ${suffix}`;
    await createClient(page, clientName);
    await createTrip(page, clientName);

    await page.getByRole("tab", { name: "Ocorrências" }).click();
    await expect(page.getByRole("button", { name: /excluir/i })).toHaveCount(0);

    await page.getByRole("button", { name: "Nova ocorrência" }).click();
    await page.fill("#occurrence-description", "Atraso por trânsito.");
    await page.fill("#occurrence-occurred-at", "2026-01-15T10:00");
    await page.getByRole("button", { name: "Registrar ocorrência" }).click();
    await expect(page.getByText("Ocorrência registrada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Aberta", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Marcar como resolvida" }).click();
    await expect(page.getByText("Ocorrência marcada como resolvida.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Resolvida", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Marcar como resolvida" })).toHaveCount(0);
  });

  test("Timeline: somente leitura, sem nenhum botão de escrita", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Timeline E2E ${suffix}`;
    await createClient(page, clientName);
    await createTrip(page, clientName);

    await page.getByRole("tab", { name: "Ocorrências" }).click();
    await page.getByRole("button", { name: "Nova ocorrência" }).click();
    await page.fill("#occurrence-description", "Evento para aparecer na timeline.");
    await page.fill("#occurrence-occurred-at", "2026-01-15T10:00");
    await page.getByRole("button", { name: "Registrar ocorrência" }).click();
    await expect(page.getByText("Ocorrência registrada.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("tab", { name: "Timeline" }).click();
    const timelinePanel = page.getByRole("tabpanel");
    // `summary` é montado pelo Backend (`list_trip_timeline.py`) como "Ocorrência registrada:
    // {tipo}" — nunca a descrição livre digitada no formulário, que não é persistida na Timeline.
    await expect(timelinePanel.getByText("Ocorrência registrada: ATRASO")).toBeVisible({ timeout: 10_000 });
    // Poucos eventos (< 50) — sem "Carregar mais" e sem nenhum outro botão: GET-only, para sempre.
    await expect(timelinePanel.getByRole("button")).toHaveCount(0);
  });

  test("Cancelar: viagem em Rascunho pode ser cancelada, e vira estado terminal sem ações", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Cancelar E2E ${suffix}`;
    await createClient(page, clientName);
    await createTrip(page, clientName);

    await page.getByRole("button", { name: "Cancelar" }).click();
    await page.fill("#command-text", "Cliente desistiu do frete.");
    await page.getByRole("button", { name: "Cancelar viagem" }).click();
    await expect(page.getByText("Viagem atualizada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Cancelada", { exact: true })).toBeVisible();

    await expect(page.getByRole("button", { name: "Cancelar" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Encerramento administrativo" })).toHaveCount(0);
  });
});
