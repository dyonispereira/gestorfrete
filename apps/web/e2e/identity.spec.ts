import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";

async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.fill("#email", email);
  await page.fill("#password", PASSWORD);
  await page.click("button[type=submit]");
  await page.waitForURL("**/dashboard");
}

test.describe("Sprint 12 — Frontend, Lote Identity", () => {
  test("cenário 1: usuário autorizado vê e executa a ação", async ({ page }) => {
    await login(page, "full@e2e-fixture.com");
    await page.goto("/usuarios");

    const createButton = page.getByRole("button", { name: "Novo usuário" });
    await expect(createButton).toBeVisible();
    await createButton.click();

    const uniqueEmail = `criado-${Date.now()}@e2e-fixture.com`;
    await page.fill("#user-nome", "Usuário Criado no E2E");
    await page.fill("#user-email", uniqueEmail);
    await page.fill("#user-password", "OutraSenha123!");
    await page.getByRole("button", { name: "Criar usuário" }).click();

    await expect(page.getByText("Usuário Criado no E2E")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(uniqueEmail)).toBeVisible();
  });

  test("cenário 2: usuário sem permissão de criação não vê o botão", async ({ page }) => {
    await login(page, "viewer@e2e-fixture.com");
    await page.goto("/usuarios");

    // Viewer holds identity_access.user.view — the list itself loads normally.
    await expect(page.getByRole("heading", { name: "Usuários" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Novo usuário" })).toHaveCount(0);
  });

  test("cenário 3: acesso direto pela URL continua bloqueado pelo backend", async ({ page }) => {
    await login(page, "noaccess@e2e-fixture.com");

    // No identity_access.* permission at all — the nav item itself is hidden…
    await expect(page.getByRole("link", { name: "Papéis" })).toHaveCount(0);

    // …but the real block is the Backend's 403, not just the missing nav link: a direct URL hit
    // must still be rejected server-side.
    await page.goto("/papeis");
    await expect(page.getByText(/não foi possível carregar/i)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("table")).toHaveCount(0);
  });

  test("cenário 4: alteração de Papel reflete no próximo request sem reload manual", async ({ page }) => {
    await login(page, "selfeditor@e2e-fixture.com");

    // Starts without identity_access.user.view — "Usuários" isn't even in the Sidebar yet.
    await expect(page.getByRole("link", { name: "Usuários" })).toHaveCount(0);

    await page.goto("/papeis");
    await page.getByRole("link", { name: "E2E Self Editor" }).click();
    await page.waitForURL("**/papeis/**");

    await page
      .locator("label", { hasText: "identity_access.user.view" })
      .locator("button[role=checkbox]")
      .click();
    await page.getByRole("button", { name: "Salvar permissões" }).click();
    await expect(page.getByText("Permissões atualizadas.")).toBeVisible({ timeout: 10_000 });

    // No page.reload() anywhere below — React Query's cache invalidation (same `["roles", roleId]`
    // key PermissionsProvider reads) must be what makes this work, purely client-side navigation.
    await expect(page.getByRole("link", { name: "Usuários" })).toBeVisible({ timeout: 10_000 });
    await page.getByRole("link", { name: "Usuários" }).click();
    await page.waitForURL("**/usuarios");
    await expect(page.getByRole("heading", { name: "Usuários" })).toBeVisible();
    await expect(page.getByText(/não foi possível carregar/i)).toHaveCount(0);
  });
});
