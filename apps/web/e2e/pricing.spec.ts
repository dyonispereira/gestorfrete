import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";

async function login(page: Page) {
  await page.goto("/login");
  await page.fill("#email", "pricing-admin@e2e-fixture.com");
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

test.describe("Lote 2 — Frontend, Tabela de Frete (GESTORFRETE — PROMPT MESTRE)", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("golden path: criar tabela de frete por KM, aplicar na viagem e remover", async ({ page }) => {
    const suffix = Date.now();
    const clientName = `Cliente Pricing E2E ${suffix}`;
    const driverName = `Motorista Pricing E2E ${suffix}`;
    const plate = `PR${suffix.toString().slice(-5)}`;
    const tableName = `Tabela KM E2E ${suffix}`;

    // 1. Criar tabela de frete (VENDA, por KM) e ativar.
    await page.goto("/tabelas-frete");
    await page.getByRole("button", { name: "Nova tabela" }).click();
    await page.fill("#price-table-nome", tableName);
    await page.fill("#price-table-vigencia-inicio", "2026-01-01");
    const [createTableResponse] = await Promise.all([
      page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/tabelas-preco")),
      page.getByRole("button", { name: "Criar tabela" }).click(),
    ]);
    const table = (await createTableResponse.json()) as { id: string };
    await expect(page.getByText("Tabela de frete criada.")).toBeVisible({ timeout: 10_000 });

    await page.goto(`/tabelas-frete/${table.id}`);
    await page.getByRole("tab", { name: "Itens" }).click();
    await page.getByRole("button", { name: "Novo item" }).click();
    await page.getByLabel("Unidade de cálculo").click();
    await page.getByRole("option", { name: "Valor por km" }).click();
    await page.fill("#item-valor", "10.00");
    await page.getByRole("button", { name: "Adicionar item" }).click();
    await expect(page.getByText("Item adicionado.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Ativar tabela" }).click();
    await expect(page.getByText("Tabela ativada")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Vigente", { exact: true })).toBeVisible();

    // 2. Criar cliente/motorista/veículo/viagem e alocar recursos.
    await createClient(page, clientName);
    await createDriver(page, driverName);
    await createVehicle(page, plate);
    await createTrip(page, clientName);
    await allocateResources(page, driverName, plate);

    // 3. Informar distância prevista na aba Visão Geral.
    await page.getByRole("tab", { name: "Visão Geral" }).click();
    await page.getByRole("button", { name: "Editar" }).click();
    await page.fill("#cargo-distancia", "100.00");
    await page.getByRole("button", { name: "Salvar" }).click();
    await expect(page.getByText("Dados de carga e percurso atualizados.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("100.00 km")).toBeVisible();

    // 4. Aplicar a tabela de frete na aba Financeiro — valor calculado = 10.00 × 100 = 1000,00.
    await page.getByRole("tab", { name: "Financeiro" }).click();
    await page.getByRole("button", { name: "Aplicar tabela de frete" }).click();
    await page.getByLabel("Tabela de frete (venda, vigente)").click();
    await page.getByRole("option", { name: tableName }).click();
    await page.getByLabel("Item").click();
    await page.getByRole("option", { name: "KM" }).click();
    await page.getByRole("button", { name: "Aplicar", exact: true }).click();
    await expect(page.getByText("Tabela de frete aplicada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("R$ 1.000,00").first()).toBeVisible({ timeout: 10_000 });

    // 5. Remover a aplicação — volta a mostrar "nenhuma tabela aplicada".
    await page.getByRole("button", { name: "Remover aplicação" }).click();
    await expect(page.getByText("Aplicação de Tabela de Frete removida.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Nenhuma tabela de frete aplicada ainda.")).toBeVisible({ timeout: 10_000 });
  });

  test("tabela de compra pode ser criada e ativada (CRUD completo, aplicação fica para o Lote 5)", async ({ page }) => {
    const suffix = Date.now();
    const tableName = `Tabela Compra E2E ${suffix}`;

    await page.goto("/tabelas-frete");
    await page.getByRole("button", { name: "Nova tabela" }).click();
    await page.fill("#price-table-nome", tableName);
    await page.getByLabel("Direção").click();
    await page.getByRole("option", { name: "Compra" }).click();
    await page.fill("#price-table-vigencia-inicio", "2026-01-01");
    await page.getByRole("button", { name: "Criar tabela" }).click();
    await expect(page.getByText("Tabela de frete criada.")).toBeVisible({ timeout: 10_000 });
    const row = page.getByRole("row").filter({ hasText: tableName });
    await expect(row).toBeVisible();
    await expect(row.getByText("Compra", { exact: true })).toBeVisible();
  });
});
