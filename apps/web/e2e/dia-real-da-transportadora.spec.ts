import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Senha123!";

async function login(page: Page) {
  await page.goto("/login");
  await page.fill("#email", "dia-real-admin@e2e-fixture.com");
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

/** V1 Operational Hardening, Parte 5 (D363) — a Categoria nasce pela própria UI, não por seed SQL. */
async function createVehicleCategory(page: Page, name: string) {
  await page.goto("/categorias-veiculo");
  await page.getByRole("button", { name: "Nova categoria" }).click();
  await page.fill("#vehicle-category-nome", name);
  await page.getByRole("button", { name: "Criar categoria" }).click();
  await expect(page.getByText("Categoria de veículo criada.")).toBeVisible({ timeout: 10_000 });
}

async function createVehicle(page: Page, plate: string, categoryName: string) {
  await page.goto("/veiculos");
  await page.getByRole("button", { name: "Novo veículo" }).click();
  await page.fill("#vehicle-plate", plate);
  await page.fill("#vehicle-renavam", uniqueDigits(11));
  await page.fill("#vehicle-fabricante", "Volvo");
  await page.fill("#vehicle-modelo", "FH540");
  await page.fill("#vehicle-ano", "2023");
  await page.getByLabel("Categoria").click();
  await page.getByRole("option", { name: categoryName }).click();
  await page.getByRole("button", { name: "Criar veículo" }).click();
  await expect(page.getByText(plate)).toBeVisible({ timeout: 10_000 });
}

async function createTrip(page: Page, clientName: string): Promise<{ id: string; codigo: string }> {
  await page.goto("/viagens");
  await page.getByRole("button", { name: "Nova viagem" }).click();
  await page.getByLabel("Cliente").click();
  await page.getByRole("option", { name: clientName }).click();

  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === "POST" && res.url().endsWith("/viagens")),
    page.getByRole("button", { name: "Criar viagem" }).click(),
  ]);
  const trip = (await response.json()) as { id: string; codigo: string };
  await expect(page.getByText("Viagem criada.")).toBeVisible({ timeout: 10_000 });
  await page.goto(`/viagens/${trip.id}`);
  return trip;
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

/** Checklist "Motorista — Saída" completo → aprovado, dispara AGUARDANDO_CHECKLIST → LIBERADA. */
async function passChecklistToLiberada(page: Page) {
  await page.getByRole("tab", { name: "Checklist" }).click();
  await page.getByRole("button", { name: "Novo checklist" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Criar checklist" }).click();
  await expect(page.getByText("Checklist criado.")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Aguardando checklist", { exact: true })).toBeVisible({ timeout: 10_000 });

  await page.getByRole("button", { name: "Iniciar preenchimento" }).click();
  await expect(page.getByText("Preenchimento iniciado.")).toBeVisible({ timeout: 10_000 });

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

async function createDelivery(page: Page) {
  await page.getByRole("tab", { name: "Entregas" }).click();
  await page.getByRole("button", { name: "Nova entrega" }).click();
  await page.fill("#delivery-order", "1");
  await page.fill("#delivery-recipient", "Destinatário E2E Dia Real");
  await page.fill("#delivery-logradouro", "Av. Teste");
  await page.fill("#delivery-cidade", "São Paulo");
  await page.fill("#delivery-uf", "SP");
  await page.fill("#delivery-cep", "01000-000");
  await page.getByRole("button", { name: "Criar entrega" }).click();
  await expect(page.getByText("Entrega criada.")).toBeVisible({ timeout: 10_000 });
}

async function registerCanhoto(page: Page) {
  await page.getByRole("tab", { name: "Entregas" }).click();
  await page.getByRole("button", { name: "Editar" }).click();
  const editDialog = page.getByRole("dialog");
  await editDialog.getByLabel("Status").click();
  await page.getByRole("option", { name: "Concluída" }).click();
  await editDialog.getByRole("button", { name: "Salvar" }).click();
  await expect(page.getByText("Entrega atualizada.")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("button", { name: "Registrar canhoto" }).click();
  await expect(page.getByText("Canhoto registrado.")).toBeVisible({ timeout: 10_000 });
}

/**
 * V1 Operational Hardening, Parte 7 — "Dia Real da Transportadora", o critério de aceite principal
 * de toda a rodada. Prova, numa única viagem, sem seed SQL de estado de negócio (só bootstrap
 * técnico de tenant/role/user, mesmo padrão de todo Lote anterior), o ciclo operacional completo
 * pedido pelo usuário: Cliente → Motorista → Categoria → Veículo → Viagem 1 → Alocação → Checklist
 * → LIBERADA → Despacho → EM_DESLOCAMENTO → Coleta → CARREGANDO → Romaneio → EM_ENTREGA → Canhoto →
 * Encerramento normal (nunca Administrativo) → FINALIZADA → KM realizado → Resultado Gerencial →
 * Veículo DISPONÍVEL novamente → Viagem 2 → aloca o MESMO veículo com sucesso.
 */
test.describe("V1 Operational Hardening — Dia Real da Transportadora", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("ciclo operacional completo: Cadastro → Viagem → Checklist → Despacho → Coleta → Romaneio → Entrega → Canhoto → Encerramento → KM → Resultado → Veículo reutilizável", async ({
    page,
  }) => {
    const suffix = Date.now();
    const categoryName = `Categoria Dia Real ${suffix}`;
    const clientName = `Cliente Dia Real ${suffix}`;
    const driverName = `Motorista Dia Real ${suffix}`;
    const plate = `DR${suffix.toString().slice(-5)}`;

    // Cadastro → Programação (preparação operacional)
    await createVehicleCategory(page, categoryName);
    await createClient(page, clientName);
    await createDriver(page, driverName);
    await createVehicle(page, plate, categoryName);

    // Viagem 1 → Alocação → Checklist → LIBERADA
    const trip = await createTrip(page, clientName);
    await allocateResources(page, driverName, plate);
    await expect(page.getByText("Planejada", { exact: true })).toBeVisible({ timeout: 10_000 });
    await passChecklistToLiberada(page);

    // Despacho (com hodômetro de saída, V1 Operational Hardening Parte 2) → EM_DESLOCAMENTO
    await page.getByRole("tab", { name: "Visão Geral" }).click();
    await page.fill("#trip-departure-odometer-km", "100000");
    await page.getByRole("button", { name: "Despachar" }).click();
    await expect(page.getByText("Viagem despachada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Em deslocamento", { exact: true })).toBeVisible();

    // Entrega registrada antes da Coleta — necessária para o Romaneio cascatear até EM_ENTREGA.
    await createDelivery(page);

    // Coleta (V1 Operational Hardening Parte 2) → CARREGANDO
    await page.getByRole("tab", { name: "Visão Geral" }).click();
    await page.getByRole("checkbox", { name: "Carga conferida" }).click();
    await page.getByRole("button", { name: "Registrar coleta" }).click();
    await expect(page.getByText("Coleta registrada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Carregando", { exact: true })).toBeVisible({ timeout: 10_000 });

    // Romaneio (V1 Operational Hardening Parte 2/3) — cascateia direto para EM_ENTREGA porque já
    // existe uma Entrega PENDENTE.
    await page.getByRole("button", { name: "Confirmar romaneio" }).click();
    const manifestDialog = page.getByRole("dialog");
    await manifestDialog.getByLabel("Descrição").fill("Pallet de caixas");
    await manifestDialog.getByLabel("Peso (kg)").fill("500");
    await manifestDialog.getByLabel("Quantidade").fill("2");
    await manifestDialog.getByRole("button", { name: "Confirmar romaneio" }).click();
    await expect(page.getByText("Romaneio confirmado.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Em entrega", { exact: true })).toBeVisible({ timeout: 10_000 });

    // Canhoto
    await registerCanhoto(page);

    // Encerramento NORMAL (nunca Administrativo) — com hodômetro de chegada → FINALIZADA.
    await page.getByRole("tab", { name: "Visão Geral" }).click();
    await page.fill("#trip-arrival-odometer-km", "100500");
    await page.getByRole("button", { name: "Finalizar" }).click();
    await expect(page.getByText("Viagem finalizada.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Finalizada", { exact: true })).toBeVisible({ timeout: 10_000 });

    // KM realizado + Resultado Gerencial — nunca "Indisponível" agora que as duas leituras de
    // fronteira (despacho + encerramento) existem.
    await page.goto("/resultados");
    await page.getByRole("tab", { name: "Viagens" }).click();
    const tripRow = page.getByRole("row").filter({ hasText: trip.codigo });
    await expect(tripRow).toBeVisible({ timeout: 10_000 });
    await expect(tripRow.getByText("500 km")).toBeVisible();
    await expect(tripRow.getByText("Indisponível")).toHaveCount(0);

    // Veículo DISPONÍVEL novamente: Viagem 2, mesmo Veículo, mesmo Motorista — a prova principal
    // desta rodada. Se a Alocação da Viagem 1 não tivesse sido encerrada (o P0 do Go-Live Audit),
    // este passo falharia com FREIGHT_VEHICLE_UNAVAILABLE.
    const clientName2 = `Cliente Dia Real 2 ${suffix}`;
    await createClient(page, clientName2);
    await createTrip(page, clientName2);
    await allocateResources(page, driverName, plate);
    await expect(page.getByText("Planejada", { exact: true })).toBeVisible({ timeout: 10_000 });
  });
});
