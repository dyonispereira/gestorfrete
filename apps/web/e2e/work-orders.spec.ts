import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";

async function login(page: Page) {
  await page.goto("/login");
  await page.fill("#email", "work-orders-admin@e2e-fixture.com");
  await page.fill("#password", PASSWORD);
  await page.click("button[type=submit]");
  await page.waitForURL("**/dashboard");
}

function uniqueDigits(length: number): string {
  return Date.now().toString().padStart(length, "0").slice(-length);
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

async function createWorkOrder(
  page: Page, plate: string, description: string, openingOdometerKm?: string
): Promise<string> {
  await page.goto("/ordens-servico");
  await page.getByRole("button", { name: "Nova ordem de serviço" }).click();
  await page.getByLabel("Veículo").click();
  await page.getByRole("option", { name: plate }).click();
  await page.fill("#work-order-problem-description", description);
  if (openingOdometerKm) {
    await page.fill("#work-order-opening-odometer", openingOdometerKm);
  }

  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/ordens-servico")),
    page.getByRole("button", { name: "Criar ordem de serviço" }).click(),
  ]);
  const workOrder = (await response.json()) as { id: string };
  await expect(page.getByText("Ordem de serviço criada.")).toBeVisible({ timeout: 10_000 });
  await page.goto(`/ordens-servico/${workOrder.id}`);
  return workOrder.id;
}

async function diagnosticar(page: Page, { needsApproval }: { needsApproval: boolean }) {
  await page.getByRole("button", { name: "Diagnosticar" }).click();
  await page.fill("#work-order-technical-diagnosis", "Diagnóstico técnico E2E.");
  if (needsApproval) {
    await page.getByRole("dialog").getByRole("checkbox").click();
  }
  await page.getByRole("button", { name: "Salvar diagnóstico" }).click();
  await expect(page.getByText("Diagnóstico registrado.")).toBeVisible({ timeout: 10_000 });
}

/**
 * Sprint 15 — Lote Frota e Manutenção, Parte 2 (Ordens de Serviço). Prova o ciclo de vida real —
 * caminho sem aprovação, caminho com aprovação de custo (reprovado → reaprovado), a guarda de
 * cancelamento, e a costura Checklist↔OS (Parte 1 estendida): Checklist "Oficina" reprovado abre
 * uma segunda OS corretiva automaticamente, sem chamada alguma a `freight` e sem SQL seed.
 */
test.describe("Sprint 15 — Frontend, Lote Frota e Manutenção (Ordens de Serviço)", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("caminho sem aprovação: aberta → diagnóstico → execução → itens → concluída → fechada", async ({ page }) => {
    const suffix = Date.now();
    const plate = `OS${suffix.toString().slice(-5)}`;

    const vehicleId = await createVehicle(page, plate);
    await createWorkOrder(page, plate, "Ruído no motor durante a partida.", "100000");
    await expect(page.getByText("Aberta", { exact: true })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("100.000 km")).toBeVisible();

    // OS aberta bloqueia a disponibilidade do veículo (EM_MANUTENCAO) — critério de aceite:
    // Disponibilidade real, não só "OS bonita no frontend".
    await page.goto("/disponibilidade");
    await expect(page.getByRole("link", { name: vehicleId })).toBeVisible({ timeout: 10_000 });
    await expect(
      page.getByRole("row").filter({ has: page.getByRole("link", { name: vehicleId }) }).getByText("Em manutenção")
    ).toBeVisible();
    await page.goBack();

    await diagnosticar(page, { needsApproval: false });
    await expect(page.getByText("Em diagnóstico", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Iniciar execução" }).click();
    await expect(page.getByText("Execução iniciada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Em execução", { exact: true })).toBeVisible();

    // Custo real: Peças + Mão de Obra Interna = Custo Total, sempre derivado dos itens.
    await page.getByRole("tab", { name: "Itens" }).click();
    await page.getByRole("button", { name: "Novo item" }).click();
    await page.fill("#work-order-item-description", "Correia dentada");
    await page.fill("#work-order-item-quantity", "1");
    await page.fill("#work-order-item-unit-value", "350");
    await page.getByRole("button", { name: "Adicionar item" }).click();
    await expect(page.getByText("Item adicionado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Correia dentada")).toBeVisible();

    await page.getByRole("button", { name: "Novo item" }).click();
    await page.getByLabel("Categoria").click();
    await page.getByRole("option", { name: "Mão de obra interna" }).click();
    await page.fill("#work-order-item-description", "Instalação e testes");
    await page.fill("#work-order-item-quantity", "2");
    await page.fill("#work-order-item-unit-value", "50");
    await page.getByRole("button", { name: "Adicionar item" }).click();
    await expect(page.getByText("Instalação e testes")).toBeVisible({ timeout: 10_000 });

    await expect(page.getByText("Custo total (sempre derivado dos itens)")).toBeVisible();
    await expect(page.getByText("R$ 450,00")).toBeVisible();

    // Hodômetro na conclusão — completa o par abertura/conclusão que alimenta o futuro plano de
    // manutenção preventiva por KM.
    await page.getByRole("button", { name: "Concluir" }).click();
    const concludeDialog = page.getByRole("dialog");
    await concludeDialog.locator("#work-order-completion-odometer").fill("100450");
    await concludeDialog.getByRole("button", { name: "Concluir ordem de serviço" }).click();
    await expect(page.getByText("Ordem de serviço concluída.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Concluída", { exact: true })).toBeVisible();
    await page.getByRole("tab", { name: "Visão Geral" }).click();
    await expect(page.getByText("100.450 km")).toBeVisible();

    // Conclusão libera o veículo de volta para Disponível.
    await page.goto("/disponibilidade");
    await expect(
      page.getByRole("row").filter({ has: page.getByRole("link", { name: vehicleId }) }).getByText("Disponível")
    ).toBeVisible({ timeout: 10_000 });
    await page.goBack();

    await page.getByRole("button", { name: "Fechar" }).click();
    await expect(page.getByText("Ordem de serviço fechada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Fechada", { exact: true })).toBeVisible();

    // O hodômetro de conclusão também virou uma Leitura de Hodômetro real do veículo (fleet).
    await page.goto(`/veiculos/${vehicleId}`);
    await page.getByRole("tab", { name: "Hodômetro" }).click();
    await expect(page.getByText("100.450 km")).toBeVisible({ timeout: 10_000 });
    await expect(page.locator(':text-is("Ordem de serviço"):visible').first()).toBeVisible();
  });

  test("caminho com aprovação: reprovar custo volta a diagnóstico, reaprovar libera execução", async ({ page }) => {
    const suffix = Date.now();
    const plate = `OA${suffix.toString().slice(-5)}`;

    await createVehicle(page, plate);
    await createWorkOrder(page, plate, "Suspensão dianteira com folga.");

    await diagnosticar(page, { needsApproval: true });
    await expect(page.getByText("Em diagnóstico", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Submeter para aprovação" }).click();
    await expect(page.getByText("Submetido para aprovação.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Aguardando aprovação", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Reprovar custo" }).click();
    const rejectDialog = page.getByRole("dialog");
    await rejectDialog.locator("#work-order-text-dialog").fill("Orçamento acima do previsto — renegociar com fornecedor.");
    await rejectDialog.getByRole("button", { name: "Reprovar custo" }).click();
    await expect(page.getByText("Custo reprovado — de volta ao diagnóstico.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Em diagnóstico", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Submeter para aprovação" }).click();
    await expect(page.getByText("Aguardando aprovação", { exact: true })).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Aprovar custo" }).click();
    await expect(page.getByText("Custo aprovado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Em execução", { exact: true })).toBeVisible();

    await page.getByRole("tab", { name: "Aprovações de Custo" }).click();
    await expect(page.getByText("Rejeitado", { exact: true })).toBeVisible();
    await expect(page.getByText("Aprovado", { exact: true })).toBeVisible();
  });

  test("guarda de cancelamento: possível antes de Em Execução, nunca depois", async ({ page }) => {
    const suffix = Date.now();
    const plateA = `OC${suffix.toString().slice(-5)}`;
    const plateB = `OD${suffix.toString().slice(-5)}`;

    const vehicleIdA = await createVehicle(page, plateA);
    await createWorkOrder(page, plateA, "Vazamento de óleo.");
    await page.getByRole("button", { name: "Cancelar" }).click();
    const cancelDialog = page.getByRole("dialog");
    await cancelDialog.locator("#work-order-text-dialog").fill("Veículo substituído — manutenção não é mais necessária.");
    await cancelDialog.getByRole("button", { name: "Cancelar ordem de serviço" }).click();
    await expect(page.getByText("Ordem de serviço cancelada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Cancelada", { exact: true })).toBeVisible();

    // Cancelamento também libera o veículo — a abertura já o havia bloqueado.
    await page.goto("/disponibilidade");
    await expect(
      page.getByRole("row").filter({ has: page.getByRole("link", { name: vehicleIdA }) }).getByText("Disponível")
    ).toBeVisible({ timeout: 10_000 });

    await createVehicle(page, plateB);
    await createWorkOrder(page, plateB, "Freio de estacionamento não trava.");
    await diagnosticar(page, { needsApproval: false });
    await page.getByRole("button", { name: "Iniciar execução" }).click();
    await expect(page.getByText("Em execução", { exact: true })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: "Cancelar" })).toHaveCount(0);
  });

  test("Checklist Oficina reprovado abre automaticamente uma OS corretiva", async ({ page }) => {
    const suffix = Date.now();
    const plate = `OW${suffix.toString().slice(-5)}`;

    await createVehicle(page, plate);
    await createWorkOrder(page, plate, "Verificação geral solicitada pela oficina.");

    await page.getByRole("tab", { name: "Checklist" }).click();
    await page.getByRole("button", { name: "Novo checklist" }).click();
    const createDialog = page.getByRole("dialog");
    await expect(createDialog.getByLabel("Tipo")).toHaveText("Oficina");
    await createDialog.getByRole("button", { name: "Criar checklist" }).click();
    await expect(page.getByText("Checklist criado.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Iniciar preenchimento" }).click();
    await expect(page.getByText("Preenchimento iniciado.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Adicionar item" }).click();
    await page.fill("#checklist-item-0", "Nível de fluido de freio");
    await page.getByLabel("Resposta").click();
    await page.getByRole("option", { name: "Não conforme" }).click();
    await page.getByRole("button", { name: "Concluir checklist" }).click();
    await expect(page.getByText("Checklist concluído.")).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "Reprovar" }).click();
    await page.fill("#checklist-reject-observacao", "Fluido de freio abaixo do nível mínimo.");
    await page.getByRole("button", { name: "Reprovar checklist" }).click();
    await expect(page.getByText("Checklist reprovado")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Reprovado", { exact: true })).toBeVisible();
    await expect(page.getByText("Pendente", { exact: true })).toBeVisible();

    // A OS corretiva nasceu sozinha da reprovação — sem chamada a `freight`, sem SQL seed.
    await page.goto("/ordens-servico");
    await expect(page.getByText("CHECKLIST_REPROVADO").first()).toBeVisible({ timeout: 10_000 });
  });
});
