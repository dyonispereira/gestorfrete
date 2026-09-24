import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";

async function login(page: Page) {
  await page.goto("/login");
  await page.fill("#email", "frota-admin@e2e-fixture.com");
  await page.fill("#password", PASSWORD);
  await page.click("button[type=submit]");
  await page.waitForURL("**/dashboard");
}

function uniqueDigits(length: number): string {
  return Date.now().toString().padStart(length, "0").slice(-length);
}

test.describe("Sprint 12 — Frontend, Lote Frota", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("golden path: criar Veículo, criar Implemento, editar Veículo", async ({ page }) => {
    const plate = `VE${Date.now().toString().slice(-5)}`;

    await page.goto("/implementos");
    await page.getByRole("button", { name: "Novo implemento" }).click();
    await page.fill("#implement-plate", `IM${Date.now().toString().slice(-5)}`);
    await page.fill("#implement-renavam", uniqueDigits(11));
    await page.fill("#implement-load-capacity", "10000");
    await page.getByLabel("Categoria").click();
    await page.getByRole("option", { name: "E2E Categoria" }).click();
    await page.getByRole("button", { name: "Criar implemento" }).click();
    await expect(page.getByText("Implemento criado.")).toBeVisible({ timeout: 10_000 });

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

    await page.getByText(plate).click();
    await page.waitForURL("**/veiculos/**");
    await page.fill("#detail-fabricante", "Scania");
    await page.getByRole("button", { name: "Salvar alterações" }).click();
    await expect(page.getByText("Veículo atualizado.")).toBeVisible({ timeout: 10_000 });
  });

  test("Veículo: preencher Ficha Técnica e confirmar persistência", async ({ page }) => {
    const plate = `VE${Date.now().toString().slice(-5)}`;
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
    await page.getByText(plate).click();
    await page.waitForURL("**/veiculos/**");

    await page.getByRole("tab", { name: "Ficha Técnica" }).click();
    await page.fill("#ts-chassis", "CHASSI-E2E-001");
    await page.fill("#ts-axles", "3");
    await page.fill("#ts-tare", "8000");
    await page.fill("#ts-capacity", "20000");
    await page.fill("#ts-gvw", "28000");
    await page.getByRole("combobox").last().click();
    await page.getByRole("option", { name: "Diesel S10" }).click();
    await page.getByRole("button", { name: "Salvar ficha técnica" }).click();
    await expect(page.getByText("Ficha técnica salva.")).toBeVisible({ timeout: 10_000 });

    await page.reload();
    await page.getByRole("tab", { name: "Ficha Técnica" }).click();
    await expect(page.locator("#ts-chassis")).toHaveValue("CHASSI-E2E-001");
  });

  test("Veículo: nova Composição encerra a anterior automaticamente (D248)", async ({ page }) => {
    const plate = `VE${Date.now().toString().slice(-5)}`;
    const implementPlate = `IM${Date.now().toString().slice(-5)}`;

    await page.goto("/implementos");
    await page.getByRole("button", { name: "Novo implemento" }).click();
    await page.fill("#implement-plate", implementPlate);
    await page.fill("#implement-renavam", uniqueDigits(11));
    await page.fill("#implement-load-capacity", "10000");
    await page.getByLabel("Categoria").click();
    await page.getByRole("option", { name: "E2E Categoria" }).click();
    await page.getByRole("button", { name: "Criar implemento" }).click();
    await expect(page.getByText("Implemento criado.")).toBeVisible({ timeout: 10_000 });

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
    await page.getByText(plate).click();
    await page.waitForURL("**/veiculos/**");

    await page.getByRole("tab", { name: "Composições" }).click();

    // Primeira composição.
    await page.getByRole("button", { name: "Nova composição" }).click();
    await page.fill("#composition-axles", "3");
    await page.getByText(implementPlate).click();
    await page.getByRole("button", { name: "Criar composição" }).click();
    await expect(page.getByText("Nova composição criada")).toBeVisible({ timeout: 10_000 });
    await page.waitForSelector("[role=dialog]", { state: "hidden" });

    const timeline = page.locator("div.border-l-2");
    await expect(timeline.getByText("Vigente", { exact: true })).toHaveCount(1);

    // Segunda composição — D248: a primeira deve virar "Encerrada" automaticamente, sem PATCH.
    await page.getByRole("button", { name: "Nova composição" }).click();
    await page.fill("#composition-axles", "3");
    await page.getByText(implementPlate).click();
    await page.getByRole("button", { name: "Criar composição" }).click();
    await expect(page.getByText("Nova composição criada")).toBeVisible({ timeout: 10_000 });
    await page.waitForSelector("[role=dialog]", { state: "hidden" });

    await expect(timeline.getByText("Vigente", { exact: true })).toHaveCount(1);
    await expect(timeline.getByText("Encerrada", { exact: true })).toHaveCount(1);
  });

  test("Veículo: registrar Leitura de Hodômetro — sem editar/excluir", async ({ page }) => {
    const plate = `VE${Date.now().toString().slice(-5)}`;
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
    await page.getByText(plate).click();
    await page.waitForURL("**/veiculos/**");

    await page.getByRole("tab", { name: "Hodômetro" }).click();
    await page.fill("#odometer-value", "123456");
    await page.getByRole("button", { name: "Registrar leitura" }).click();
    await expect(page.getByText("Leitura registrada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("123.456 km")).toBeVisible();

    await expect(page.getByRole("button", { name: "Editar" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Excluir" })).toHaveCount(0);
  });

  test("Disponibilidade: tela somente leitura, sem nenhuma ação", async ({ page }) => {
    await page.goto("/disponibilidade");
    await expect(page.getByRole("heading", { name: "Disponibilidade" })).toBeVisible();
    await expect(page.getByText("Consulta somente leitura")).toBeVisible();

    // O único <button> na página deve ser o filtro de status — nenhuma ação de escrita.
    const mainButtons = page.locator("main button");
    await expect(mainButtons).toHaveCount(1);
    await expect(mainButtons.first()).toHaveAttribute("role", "combobox");
  });
});
