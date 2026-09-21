import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";

const TRIP_ID = "fca10000-0000-0000-0000-0000000000d1";
const CTE_RASCUNHO_ID = "fca10000-0000-0000-0000-000000001c01"; // 1001 — golden path validar→assinar→transmitir
const CTE_INUTILIZAR_ID = "fca10000-0000-0000-0000-000000001c02"; // 1002 — ramo inutilizar
const CTE_AUTORIZADO_ID = "fca10000-0000-0000-0000-000000001c03"; // 1003 — cancelar/CC-e/MDF-e

/** Limpa a sessão antes de navegar para `/login` — a página redireciona para `/dashboard` no
 * `useEffect` se já houver um token válido em `localStorage`, o que quebraria uma re-login no meio
 * do teste (cenário de Configuração Fiscal com dois usuários). */
async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
  await page.fill("#email", email);
  await page.fill("#password", PASSWORD);
  await page.click("button[type=submit]");
  await page.waitForURL("**/dashboard");
}

/**
 * Sprint 14 — Frontend, Lote Documentos Fiscais. Ao contrário de todo Lote anterior, os CT-e sob
 * teste são semeados diretamente via SQL (`fiscal-seed.sql`), não criados pela UI — não existe
 * `POST /ctes` (D396), CT-e só nasce via despacho de Viagem, e despacho exige `LIBERADA`, já
 * provado inalcançável pela UI na Lote Operação (sem módulo de Checklist ainda). Os testes abaixo
 * têm ordem intencional: `fullyParallel: false`/`workers: 1` (playwright.config.ts) roda os
 * arquivos em sequência, e aqui cada teste consome o estado deixado pelo anterior no mesmo CT-e
 * semeado — não são independentes entre si como nos Lotes anteriores, de propósito, para não
 * precisar semear uma dúzia de CT-e só para isolar cada cenário.
 *
 * `TRANSMITIDO → AUTORIZADO`/`DENEGADO` — Reconciliado (Lote Fiscal, Parte 2.2, D397 fechado):
 * ganhou rota HTTP real (`commands/receive-sefaz-response`, `SandboxSefazGateway`). O primeiro
 * teste abaixo agora avança até lá, em vez de parar em `TRANSMITIDO`.
 */
test.describe("Sprint 14 — Frontend, Lote Documentos Fiscais", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, "fiscal-admin@e2e-fixture.com");
  });

  test("CT-e: validar → assinar → transmitir → simular resposta SEFAZ → Cancelar liberado", async ({ page }) => {
    await page.goto(`/ctes/${CTE_RASCUNHO_ID}`);
    await expect(page.getByText("Rascunho", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Validar" }).click();
    await expect(page.getByText("CT-e validado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Validado", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Assinar" }).click();
    await expect(page.getByText("CT-e assinado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Assinado", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Transmitir" }).click();
    await expect(page.getByText("CT-e transmitido à SEFAZ.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Transmitido", { exact: true })).toBeVisible();

    // Antes de TRANSMITIDO, "Simular resposta SEFAZ" nunca aparece — só "Cancelar" exige
    // AUTORIZADO, mas o botão de simulação em si só existe em TRANSMITIDO (gate correto).
    await expect(page.getByRole("button", { name: "Cancelar" })).toHaveCount(0);

    // D397, fechado (Lote Fiscal, Parte 2.2) — rota HTTP real, SandboxSefazGateway sempre autoriza.
    await page.getByRole("button", { name: "Simular resposta SEFAZ" }).click();
    await expect(page.getByText("Resposta da SEFAZ recebida (simulada).")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Autorizado", { exact: true })).toBeVisible();

    // Só agora, com AUTORIZADO de verdade, "Cancelar" aparece — e "Simular resposta SEFAZ" some
    // (não é mais TRANSMITIDO).
    await expect(page.getByRole("button", { name: "Cancelar" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Simular resposta SEFAZ" })).toHaveCount(0);

    // Cancela também este CT-e (1001) — sem isso, ele ficaria AUTORIZADO permanentemente e
    // quebraria a premissa do teste de MDF-e mais abaixo ("nenhum CT-e Autorizado disponível" só é
    // genuíno se todos os três CT-e semeados desta viagem — 1001/1002/1003 — não estiverem mais
    // AUTORIZADO ao final deste arquivo).
    await page.getByRole("button", { name: "Cancelar" }).click();
    await page.fill("#cte-cancel-notes", "Cancelado ao final do teste — não deixar AUTORIZADO permanente.");
    await page.getByRole("button", { name: "Cancelar CT-e" }).click();
    await expect(page.getByText("CT-e cancelado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Cancelado", { exact: true })).toBeVisible();
  });

  test("CT-e: inutilizar a partir de Rascunho vira estado terminal, sem mais comandos", async ({ page }) => {
    await page.goto(`/ctes/${CTE_INUTILIZAR_ID}`);
    await page.getByRole("button", { name: "Inutilizar" }).click();
    await expect(page.getByText("CT-e inutilizado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Inutilizado", { exact: true })).toBeVisible();

    for (const label of ["Validar", "Assinar", "Transmitir", "Inutilizar", "Cancelar"]) {
      await expect(page.getByRole("button", { name: label })).toHaveCount(0);
    }
  });

  test("NF-e Referenciada: sem gate de status do CT-e pai, sem excluir", async ({ page }) => {
    await page.goto(`/ctes/${CTE_INUTILIZAR_ID}`); // já Inutilizado — prova que não há gate de status
    await page.getByRole("tab", { name: "NF-e Referenciada" }).click();

    await page.getByRole("button", { name: "Referenciar NF-e" }).click();
    await page.fill("#nfe-access-key", "35260800000000000001550010000000032000000042");
    await page.getByRole("button", { name: "Adicionar" }).click();
    await expect(page.getByText("NF-e referenciada adicionada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("35260800000000000001550010000000032000000042")).toBeVisible();

    await expect(page.getByRole("button", { name: /excluir/i })).toHaveCount(0);
  });

  test("MDF-e: criar consolidando um CT-e Autorizado da mesma viagem", async ({ page }) => {
    await page.goto("/mdfes");
    await page.getByRole("button", { name: "Novo MDF-e" }).click();

    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Viagem").click();
    await page.getByRole("option", { name: "VG-E2EFISCAL-001" }).click();
    await expect(dialog.getByText("1003 — 1")).toBeVisible({ timeout: 10_000 });
    await dialog.getByText("1003 — 1").click();

    // O drawer só fecha (não navega, mesma escolha de design do TripFormDrawer) — captura o `id`
    // direto da resposta do `POST /mdfes` para ir ao detalhe, igual `createTrip` em viagens.spec.ts.
    const [response] = await Promise.all([
      page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/mdfes")),
      dialog.getByRole("button", { name: "Criar MDF-e" }).click(),
    ]);
    const mdfe = (await response.json()) as { id: string };
    await expect(page.getByText("MDF-e criado.")).toBeVisible({ timeout: 10_000 });

    await page.goto(`/mdfes/${mdfe.id}`);
    // O `trip_id` compartilha o mesmo prefixo `fca10000` de todo UUID deste fixture — âncora no
    // badge-link do CT-e vinculado especificamente, não em qualquer texto com esse prefixo.
    await expect(page.getByRole("link", { name: CTE_AUTORIZADO_ID.slice(0, 8) })).toBeVisible();
  });

  test("CT-e Autorizado: Carta de Correção e Cancelar", async ({ page }) => {
    await page.goto(`/ctes/${CTE_AUTORIZADO_ID}`);
    await expect(page.getByText("Autorizado", { exact: true })).toBeVisible();

    await page.getByRole("tab", { name: "Correções" }).click();
    await page.getByRole("button", { name: "Nova carta de correção" }).click();
    await page.fill("#correction-text", "Correção do endereço de destino — erro formal.");
    await page.getByRole("button", { name: "Emitir carta" }).click();
    await expect(page.getByText("Carta de correção emitida.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Carta #1")).toBeVisible();

    // Cancelar depois da carta — CT-e 1003 é o único AUTORIZADO da viagem; cancelá-lo aqui é o que
    // torna o próximo teste (MDF-e sem CT-e disponível) um cenário genuíno, não fabricado.
    await page.getByRole("tab", { name: "Visão Geral" }).click();
    await page.getByRole("button", { name: "Cancelar" }).click();
    await page.fill("#cte-cancel-notes", "Frete cancelado pelo cliente.");
    await page.getByRole("button", { name: "Cancelar CT-e" }).click();
    await expect(page.getByText("CT-e cancelado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Cancelado", { exact: true })).toBeVisible();

    for (const label of ["Validar", "Assinar", "Transmitir", "Inutilizar", "Cancelar"]) {
      await expect(page.getByRole("button", { name: label })).toHaveCount(0);
    }
  });

  test("MDF-e: sem CT-e Autorizado disponível, formulário genuinamente bloqueado", async ({ page }) => {
    // Dos três CT-e semeados nesta viagem: 1001 foi autorizado e cancelado no primeiro teste deste
    // arquivo (Reconciliado, Lote Fiscal Parte 2.2), 1002 foi inutilizado, 1003 foi autorizado e
    // cancelado no teste de Carta de Correção — nenhum CT-e Autorizado sobra para consolidar, um
    // bloqueio real do picker, não um cenário fabricado.
    await page.goto("/mdfes");
    await page.getByRole("button", { name: "Novo MDF-e" }).click();

    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Viagem").click();
    await page.getByRole("option", { name: "VG-E2EFISCAL-001" }).click();
    await expect(dialog.getByText("Nenhum CT-e Autorizado nesta viagem ainda.")).toBeVisible({ timeout: 10_000 });
    await expect(dialog.getByRole("button", { name: "Criar MDF-e" })).toBeDisabled();
  });

  test("Configuração Fiscal: campo editável persiste; sem permissão, campo fica desabilitado", async ({ page }) => {
    await page.goto("/configuracao-fiscal");
    await page.fill("#fiscal-config-tax-regime", "LUCRO_PRESUMIDO");
    await page.getByRole("button", { name: "Salvar regime tributário" }).click();
    await expect(page.getByText("Regime tributário atualizado.")).toBeVisible({ timeout: 10_000 });
    await page.reload();
    await expect(page.locator("#fiscal-config-tax-regime")).toHaveValue("LUCRO_PRESUMIDO");

    await login(page, "fiscal-viewer@e2e-fixture.com");
    await page.goto("/configuracao-fiscal");
    await expect(page.locator("#fiscal-config-tax-regime")).toBeDisabled();
    await expect(page.locator("#fiscal-config-certificate-expires")).toBeDisabled();
    await expect(page.locator("#fiscal-config-cte-series")).toBeDisabled();
    await expect(page.getByRole("button", { name: /^Salvar/ })).toHaveCount(0);
  });

  test("Eventos Fiscais: somente leitura, mostra o evento real da simulação SEFAZ deste arquivo", async ({ page }) => {
    // Reconciliado (Lote Fiscal, Parte 2.2) — antes deste Lote, "Simular resposta SEFAZ" não tinha
    // rota HTTP, então esta lista ficava genuinamente vazia em todo ambiente de teste. O primeiro
    // teste deste arquivo agora aciona `commands/receive-sefaz-response`, que grava um Evento
    // Fiscal real (RESPOSTA/SUCESSO) — a lista deixa de estar vazia porque o gap foi fechado, não
    // porque o teste passou a inventar dado.
    await page.goto("/eventos-fiscais");
    await expect(page.getByRole("row").filter({ hasText: "RESPOSTA" }).first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("SUCESSO").first()).toBeVisible();
    // 100% somente leitura mesmo com dado real presente — nenhum botão de ação na tabela.
    await expect(page.getByRole("main").getByRole("button")).toHaveCount(0);
  });
});
