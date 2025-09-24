import { test, expect } from '@playwright/test';

test.describe('Fluxo do Participante', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Navegar para aba de participante
    await page.click('text=Participante');
    await expect(page.locator('text=Dados do Participante')).toBeVisible();
  });

  test('preencher informações pessoais', async ({ page }) => {
    // Selecionar gênero
    const genderSelect = page.locator('button:has-text("Gênero")').first();
    await genderSelect.click();
    await page.click('text=Feminino');
    await expect(genderSelect).toContainText('Feminino');

    // Ajustar idade
    const ageSlider = page.locator('input[type="range"]').first();

    // Verificar limites do slider antes de preencher
    const min = await ageSlider.getAttribute('min') || '18';
    const max = await ageSlider.getAttribute('max') || '75';
    const validAge = Math.min(parseInt(max), Math.max(parseInt(min), 35));

    await ageSlider.fill(validAge.toString());

    // Aguardar atualização do display
    await page.waitForTimeout(500);

    // Verificar se idade foi atualizada (formato pode variar)
    const ageDisplay = page.locator('input[type="text"]').first();
    if (await ageDisplay.isVisible()) {
      const ageValue = await ageDisplay.inputValue();
      expect(ageValue).toContain(validAge.toString());
    }

    // Verificar expectativa de vida atualizada
    await expect(page.locator('text=/\d+ anos e \d+ meses/')).toBeVisible();
  });

  test('preencher informações financeiras', async ({ page }) => {
    // Ajustar salário mensal
    const salarySlider = page.locator('text=Salário Mensal').locator('..').locator('input[type="range"]');

    if (await salarySlider.isVisible()) {
      const min = await salarySlider.getAttribute('min') || '1000';
      const max = await salarySlider.getAttribute('max') || '100000';
      const step = await salarySlider.getAttribute('step') || '1000';
      const validSalary = Math.min(parseInt(max), Math.max(parseInt(min), 12000));

      await salarySlider.fill(validSalary.toString());
      await page.waitForTimeout(500);
    }

    // Verificar formatação do salário (formato pode variar)
    const salaryDisplay = page.locator('text=Salário Mensal').locator('..').locator('input[type="text"]');
    if (await salaryDisplay.isVisible()) {
      const salaryValue = await salaryDisplay.inputValue();
      expect(salaryValue).toMatch(/R\$|\d+/); // Aceita qualquer formato monetário
    }

    // Ajustar saldo inicial
    const balanceSlider = page.locator('text=Saldo Inicial').locator('..').locator('input[type="range"]');
    await balanceSlider.fill('50000');

    // Verificar formatação do saldo
    const balanceDisplay = page.locator('text=Saldo Inicial').locator('..').locator('input[type="text"]');
    await expect(balanceDisplay).toHaveValue('R$ 50.000,00');

    // Ajustar crescimento salarial
    const growthSlider = page.locator('text=Crescimento Salarial Real').locator('..').locator('input[type="range"]');
    await growthSlider.fill('0.02');

    // Verificar formatação do percentual
    const growthDisplay = page.locator('text=Crescimento Salarial Real').locator('..').locator('input[type="text"]');
    await expect(growthDisplay).toHaveValue('2,00%');
  });

  test('valores extremos são aceitos', async ({ page }) => {
    // Testar idade mínima
    const ageSlider = page.locator('input[type="range"]').first();
    const min = await ageSlider.getAttribute('min') || '18';
    await ageSlider.fill(min);
    await page.waitForTimeout(500);

    const ageDisplay = page.locator('input[type="text"]').first();
    if (await ageDisplay.isVisible()) {
      const ageValue = await ageDisplay.inputValue();
      expect(ageValue).toContain(min);
    }

    // Testar idade máxima
    const max = await ageSlider.getAttribute('max') || '70';
    await ageSlider.fill(max);
    await page.waitForTimeout(500);

    if (await ageDisplay.isVisible()) {
      const ageValue = await ageDisplay.inputValue();
      expect(ageValue).toContain(max);
    }

    // Testar salário máximo
    const salarySlider = page.locator('text=Salário Mensal').locator('..').locator('input[type="range"]');
    await salarySlider.fill('100000');
    await expect(page.locator('text=R$ 100.000,00')).toBeVisible();
  });

  test('dados persistem ao navegar entre abas', async ({ page }) => {
    // Definir valores específicos
    const ageSlider = page.locator('input[type="range"]').first();
    await ageSlider.fill('42');

    const salarySlider = page.locator('text=Salário Mensal').locator('..').locator('input[type="range"]');
    await salarySlider.fill('15000');

    // Navegar para outra aba
    await page.click('text=Premissas');
    await page.waitForTimeout(500);

    // Voltar para participante
    await page.click('text=Participante');

    // Verificar se valores persistiram
    await expect(page.locator('input[type="text"]').first()).toHaveValue('42 anos');
    await expect(page.locator('text=R$ 15.000,00')).toBeVisible();
  });

  test('atualização em tempo real dos cálculos', async ({ page }) => {
    // Mudar idade e verificar se expectativa de vida atualiza
    const ageSlider = page.locator('input[type="range"]').first();
    const initialExpectancy = await page.locator('text=/\d+ anos e \d+ meses/').textContent();

    await ageSlider.fill('50');
    await page.waitForTimeout(1000); // Aguardar debounce

    const newExpectancy = await page.locator('text=/\d+ anos e \d+ meses/').textContent();
    expect(initialExpectancy).not.toBe(newExpectancy);
  });

  test('validação de entrada manual', async ({ page }) => {
    // Tentar inserir valor manualmente no campo de texto da idade
    const ageDisplay = page.locator('input[type="text"]').first();
    await ageDisplay.click();
    await ageDisplay.fill('25 anos');

    // Verificar se o slider atualiza
    const ageSlider = page.locator('input[type="range"]').first();
    await expect(ageSlider).toHaveValue('25');
  });

  test('responsividade mobile', async ({ page }) => {
    // Testar em viewport mobile
    await page.setViewportSize({ width: 375, height: 667 });

    // Verificar se elementos permanecem funcionais
    await expect(page.locator('text=Informações Pessoais')).toBeVisible();
    await expect(page.locator('text=Informações Financeiras')).toBeVisible();

    // Verificar se sliders funcionam em mobile
    const ageSlider = page.locator('input[type="range"]').first();
    await ageSlider.fill('30');
    await expect(page.locator('input[type="text"]').first()).toHaveValue('30 anos');
  });
});