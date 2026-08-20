import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";

async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.fill("#email", email);
  await page.fill("#password", PASSWORD);
  await page.click("button[type=submit]");
  await page.waitForURL("**/dashboard");
}

/** 11/14-digit numeric strings, unique per run — real CPF/CNPJ checksum isn't validated by the Backend (plain `str` field). */
function uniqueDigits(length: number): string {
  return Date.now().toString().padStart(length, "0").slice(-length);
}

test.describe("Sprint 12 — Frontend, Lote Cadastros", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, "cadastros-admin@e2e-fixture.com");
  });

  test("golden path: criar Cliente, Fornecedor, Motorista, Funcionário e Centro de Custo", async ({ page }) => {
    const suffix = Date.now();

    await page.goto("/clientes");
    await page.getByRole("button", { name: "Novo cliente" }).click();
    await page.fill("#client-razao-social", `Cliente E2E ${suffix}`);
    await page.fill("#client-document", uniqueDigits(14));
    await page.getByRole("button", { name: "Criar cliente" }).click();
    await expect(page.getByText(`Cliente E2E ${suffix}`)).toBeVisible({ timeout: 10_000 });

    await page.goto("/fornecedores");
    await page.getByRole("button", { name: "Novo fornecedor" }).click();
    await page.fill("#supplier-razao-social", `Fornecedor E2E ${suffix}`);
    await page.fill("#supplier-cnpj", uniqueDigits(14));
    await page.getByRole("button", { name: "Criar fornecedor" }).click();
    await expect(page.getByText(`Fornecedor E2E ${suffix}`)).toBeVisible({ timeout: 10_000 });

    await page.goto("/motoristas");
    await page.getByRole("button", { name: "Novo motorista" }).click();
    await page.fill("#driver-nome", `Motorista E2E ${suffix}`);
    await page.fill("#driver-cpf", uniqueDigits(11));
    await page.getByRole("button", { name: "Criar motorista" }).click();
    await expect(page.getByText(`Motorista E2E ${suffix}`)).toBeVisible({ timeout: 10_000 });

    await page.goto("/funcionarios");
    await page.getByRole("button", { name: "Novo funcionário" }).click();
    await page.fill("#employee-nome", `Funcionário E2E ${suffix}`);
    await page.fill("#employee-cargo", "Analista");
    await page.getByRole("button", { name: "Criar funcionário" }).click();
    await expect(page.getByText(`Funcionário E2E ${suffix}`)).toBeVisible({ timeout: 10_000 });

    // Edit — golden path includes confirming a change actually persists, not just create.
    await page.getByText(`Funcionário E2E ${suffix}`).click();
    await page.waitForURL("**/funcionarios/**");
    await page.fill("#detail-cargo", "Analista Sênior");
    await page.getByRole("button", { name: "Salvar alterações" }).click();
    await expect(page.getByText("Funcionário atualizado.")).toBeVisible({ timeout: 10_000 });
    await page.reload();
    await expect(page.locator("#detail-cargo")).toHaveValue("Analista Sênior");

    await page.goto("/centros-custo");
    await page.getByRole("button", { name: "Novo centro de custo" }).click();
    await page.fill("#cost-center-nome", `Centro E2E ${suffix}`);
    await page.fill("#cost-center-accounting-code", `1.${suffix}`);
    await page.getByRole("button", { name: "Criar centro de custo" }).click();
    await expect(page.getByText(`Centro E2E ${suffix}`)).toBeVisible({ timeout: 10_000 });
  });

  test("Cliente: adicionar Endereço e Contato pela tela de detalhe", async ({ page }) => {
    const suffix = Date.now();
    await page.goto("/clientes");
    await page.getByRole("button", { name: "Novo cliente" }).click();
    await page.fill("#client-razao-social", `Cliente Endereco E2E ${suffix}`);
    await page.fill("#client-document", uniqueDigits(14));
    await page.getByRole("button", { name: "Criar cliente" }).click();
    await page.getByText(`Cliente Endereco E2E ${suffix}`).click();
    await page.waitForURL("**/clientes/**");

    await page.getByRole("tab", { name: "Endereços" }).click();
    await page.getByRole("button", { name: "Novo endereço" }).click();
    await page.fill("#address-logradouro", "Av. Paulista");
    await page.fill("#address-bairro", "Bela Vista");
    await page.fill("#address-cidade", "São Paulo");
    await page.fill("#address-uf", "SP");
    await page.fill("#address-cep", "01310-100");
    await page.getByRole("button", { name: "Salvar" }).click();
    await expect(page.getByText("Av. Paulista")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("tab", { name: "Contatos" }).click();
    await page.getByRole("button", { name: "Novo contato" }).click();
    await page.fill("#contact-nome", "Fulano de Tal");
    await page.getByRole("button", { name: "Salvar" }).click();
    await expect(page.getByText("Fulano de Tal")).toBeVisible({ timeout: 10_000 });
  });

  test("Motorista: bloquear e desbloquear muda a situação exibida", async ({ page }) => {
    const suffix = Date.now();
    await page.goto("/motoristas");
    await page.getByRole("button", { name: "Novo motorista" }).click();
    await page.fill("#driver-nome", `Motorista Bloqueio E2E ${suffix}`);
    await page.fill("#driver-cpf", uniqueDigits(11));
    await page.getByRole("button", { name: "Criar motorista" }).click();
    await page.getByText(`Motorista Bloqueio E2E ${suffix}`).click();
    await page.waitForURL("**/motoristas/**");

    await expect(page.getByText("Apto", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Bloquear" }).click();
    await page.locator("[role=alertdialog]").getByRole("button", { name: "Bloquear" }).click();
    await expect(page.getByText("Bloqueado", { exact: true })).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Desbloquear" }).click();
    await expect(page.getByText("Apto", { exact: true })).toBeVisible({ timeout: 10_000 });
  });

  test("Centro de Custo: tela de detalhe nunca tem botão de excluir", async ({ page }) => {
    const suffix = Date.now();
    await page.goto("/centros-custo");
    await page.getByRole("button", { name: "Novo centro de custo" }).click();
    await page.fill("#cost-center-nome", `Centro Delete Check E2E ${suffix}`);
    await page.fill("#cost-center-accounting-code", `2.${suffix}`);
    await page.getByRole("button", { name: "Criar centro de custo" }).click();
    await page.getByText(`Centro Delete Check E2E ${suffix}`).click();
    await page.waitForURL("**/centros-custo/**");

    await expect(page.getByText("Sem excluir", { exact: false })).toBeVisible();
    await expect(page.getByRole("button", { name: /excluir/i })).toHaveCount(0);
  });
});
