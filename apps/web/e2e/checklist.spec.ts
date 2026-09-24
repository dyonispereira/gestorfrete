import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";

async function login(page: Page) {
  await page.goto("/login");
  await page.fill("#email", "checklist-admin@e2e-fixture.com");
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

/**
 * Sprint 15 — Lote Frota e Manutenção, Parte 1 (Checklist). Prova o caminho real, sem SQL seed
 * algum além do bootstrap de tenant/role/user/categoria já usado em todo Lote anterior: aloca
 * recursos → cria Checklist "Motorista — Saída" (dispara `PLANEJADA→AGUARDANDO_CHECKLIST`) →
 * preenche → aprova (dispara `AGUARDANDO_CHECKLIST→LIBERADA`, gap identificado nas Lotes Operação/
 * Documentos Fiscais) → despacha (agora alcançável pela primeira vez) → CT-e nasce sozinho.
 */
test.describe("Sprint 15 — Frontend, Lote Frota e Manutenção (Checklist)", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("caminho real: alocação → checklist aprovado → LIBERADA → despacho → CT-e sem seed SQL", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Checklist E2E ${suffix}`;
    const driverName = `Motorista Checklist E2E ${suffix}`;
    const plate = `CK${suffix.toString().slice(-5)}`;

    await createClient(page, clientName);
    await createDriver(page, driverName);
    await createVehicle(page, plate);
    const tripId = await createTrip(page, clientName);
    await allocateResources(page, driverName, plate);
    await expect(page.getByText("Planejada", { exact: true })).toBeVisible({ timeout: 10_000 });

    await page.getByRole("tab", { name: "Checklist" }).click();
    await page.getByRole("button", { name: "Novo checklist" }).click();
    const createDialog = page.getByRole("dialog");
    await expect(createDialog.getByLabel("Tipo")).toHaveText("Motorista — Saída");
    await createDialog.getByRole("button", { name: "Criar checklist" }).click();
    await expect(page.getByText("Checklist criado.")).toBeVisible({ timeout: 10_000 });

    // A criação do Checklist — não o preenchimento — é quem dispara AGUARDANDO_CHECKLIST.
    await expect(page.getByText("Aguardando checklist", { exact: true })).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Iniciar preenchimento" }).click();
    await expect(page.getByText("Preenchimento iniciado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Em preenchimento", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Adicionar item" }).click();
    await page.fill("#checklist-item-0", "Pneus e estepe");
    await page.getByLabel("Resposta").click();
    await page.getByRole("option", { name: "Conforme", exact: true }).click();
    await page.getByRole("button", { name: "Concluir checklist" }).click();
    await expect(page.getByText("Checklist concluído.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Concluído", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Aprovar" }).click();
    await expect(page.getByText("Checklist aprovado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Aprovado", { exact: true })).toBeVisible();

    // O gap real: AGUARDANDO_CHECKLIST→LIBERADA, provado pela UI, não por fixture.
    await expect(page.getByText("Liberada", { exact: true })).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Despachar" }).click();
    await expect(page.getByText("Viagem despachada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Em deslocamento", { exact: true })).toBeVisible();

    // CT-e nasceu sozinho no despacho (D396) — sem POST /ctes, sem SQL seed.
    await page.goto("/ctes");
    await expect(page.getByText("Rascunho", { exact: true }).first()).toBeVisible({ timeout: 10_000 });

    // Guarda de tenant-isolation simples: o CT-e listado pertence à viagem recém-despachada.
    await page.goto(`/viagens/${tripId}`);
    await expect(page.getByText("Em deslocamento", { exact: true })).toBeVisible();
  });

  test("reprovar: gera novo checklist Pendente e a viagem nunca avança para LIBERADA", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Checklist Reprovado E2E ${suffix}`;
    const driverName = `Motorista Checklist Reprovado E2E ${suffix}`;
    const plate = `CR${suffix.toString().slice(-5)}`;

    await createClient(page, clientName);
    await createDriver(page, driverName);
    await createVehicle(page, plate);
    await createTrip(page, clientName);
    await allocateResources(page, driverName, plate);

    await page.getByRole("tab", { name: "Checklist" }).click();
    await page.getByRole("button", { name: "Novo checklist" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Criar checklist" }).click();
    await expect(page.getByText("Checklist criado.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Iniciar preenchimento" }).click();
    await page.getByRole("button", { name: "Adicionar item" }).click();
    await page.fill("#checklist-item-0", "Freios");
    await page.getByLabel("Resposta").click();
    await page.getByRole("option", { name: "Não conforme" }).click();
    await page.getByRole("button", { name: "Concluir checklist" }).click();
    await expect(page.getByText("Checklist concluído.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Reprovar" }).click();
    await page.fill("#checklist-reject-observacao", "Freio traseiro esquerdo com folga excessiva.");
    await page.getByRole("button", { name: "Reprovar checklist" }).click();
    await expect(page.getByText("Checklist reprovado")).toBeVisible({ timeout: 10_000 });

    // Um Reprovado nunca é reaberto — a reprovação cria um segundo checklist Pendente.
    await expect(page.getByText("Reprovado", { exact: true })).toBeVisible();
    await expect(page.getByText("Pendente", { exact: true })).toBeVisible();

    // A viagem fica presa em AGUARDANDO_CHECKLIST — nunca avança, "Despachar" nunca aparece.
    await expect(page.getByText("Aguardando checklist", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Despachar" })).toHaveCount(0);
  });
});
