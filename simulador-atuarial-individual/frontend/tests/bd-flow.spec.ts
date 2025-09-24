import { test, expect } from '@playwright/test';
import { navigateToTab, waitForCalculations, fillSliderWithValidation, waitForMonetaryValue } from './helpers/test-utils';

test.describe('Fluxo Completo BD (Benefício Definido)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Configurar para plano BD
    await page.click('text=Plano');
    const planTypeSelect = page.locator('select').filter({ hasText: /BD|CD/ }).first();
    if (await planTypeSelect.isVisible()) {
      await planTypeSelect.selectOption('BD');
    }
  });

  test('configuração completa de plano BD com valor fixo', async ({ page }) => {
    // Etapa 1: Configurar plano
    await page.click('text=Plano');

    // Selecionar modalidade valor fixo
    const modalitySelect = page.locator('select').filter({ hasText: /Valor Fixo|Taxa de Reposição/ });
    if (await modalitySelect.isVisible()) {
      await modalitySelect.selectOption('VALUE');
    }

    // Definir benefício alvo
    const benefitSlider = page.locator('text=Benefício Alvo').locator('..').locator('input[type="range"]');
    if (await benefitSlider.isVisible()) {
      const min = await benefitSlider.getAttribute('min') || '1000';
      const max = await benefitSlider.getAttribute('max') || '50000';
      const validBenefit = Math.min(parseInt(max), Math.max(parseInt(min), 6000));

      await benefitSlider.fill(validBenefit.toString());
      await page.waitForTimeout(500);

      // Verifica se valor foi atualizado (formato pode variar)
      await expect(page.locator('text=/R\\$|' + validBenefit + '/')).toBeVisible({ timeout: 2000 });
    }

    // Etapa 2: Participante
    await page.click('text=Participante');

    // Idade
    const ageSlider = page.locator('input[type="range"]').first();
    const min = await ageSlider.getAttribute('min') || '18';
    const max = await ageSlider.getAttribute('max') || '75';
    const validAge = Math.min(parseInt(max), Math.max(parseInt(min), 35));
    await ageSlider.fill(validAge.toString());

    // Salário
    const salarySlider = page.locator('text=Salário Mensal').locator('..').locator('input[type="range"]');
    if (await salarySlider.isVisible()) {
      const min = await salarySlider.getAttribute('min') || '1000';
      const max = await salarySlider.getAttribute('max') || '100000';
      const validSalary = Math.min(parseInt(max), Math.max(parseInt(min), 10000));
      await salarySlider.fill(validSalary.toString());
    }

    // Etapa 3: Premissas
    await page.click('text=Premissas');

    // Taxa de contribuição
    const contributionSlider = page.locator('text=Taxa de Contribuição').locator('..').locator('input[type="range"]');
    if (await contributionSlider.isVisible()) {
      const min = parseFloat(await contributionSlider.getAttribute('min') || '0.01');
      const max = parseFloat(await contributionSlider.getAttribute('max') || '0.30');
      const step = parseFloat(await contributionSlider.getAttribute('step') || '0.01');
      const validRate = Math.min(max, Math.max(min, 0.11));

      await contributionSlider.fill(validRate.toString());
      await page.waitForTimeout(500);
    }

    // Idade de aposentadoria
    const retirementSlider = page.locator('text=Idade de Aposentadoria').locator('..').locator('input[type="range"]');
    if (await retirementSlider.isVisible()) {
      const min = parseInt(await retirementSlider.getAttribute('min') || '55');
      const max = parseInt(await retirementSlider.getAttribute('max') || '75');
      const validAge = Math.min(max, Math.max(min, 65));
      await retirementSlider.fill(validAge.toString());
    }

    // Etapa 4: Verificar resultados
    await navigateToTab(page, 'Resultados');
    await waitForCalculations(page);

    // Verificar se resultados são exibidos
    await expect(page.locator('text=/RMBA|Reserva/')).toBeVisible({ timeout: 10000 });
    await waitForMonetaryValue(page);
  });

  test('plano BD com taxa de reposição', async ({ page }) => {
    // Configurar plano para taxa de reposição
    await page.click('text=Plano');

    const modalitySelect = page.locator('select').filter({ hasText: /Taxa de Reposição/ });
    if (await modalitySelect.isVisible()) {
      await modalitySelect.selectOption('REPLACEMENT_RATE');
    }

    // Definir taxa de reposição
    const replacementSlider = page.locator('text=Taxa de Reposição').locator('..').locator('input[type="range"]');
    if (await replacementSlider.isVisible()) {
      await replacementSlider.fill('0.7');
      await expect(page.locator('text=70,00%')).toBeVisible();
    }

    // Configurar participante
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('30');

    const salarySlider = page.locator('text=Salário Mensal').locator('..').locator('input[type="range"]');
    await salarySlider.fill('8000');

    // Ver resultados
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);

    // Verificar cálculos
    await expect(page.locator('text=/Taxa de Reposição/')).toBeVisible({ timeout: 10000 });
  });

  test('análise de suficiência financeira BD', async ({ page }) => {
    // Configurar participante básico
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('40');

    // Configurar premissas
    await page.click('text=Premissas');

    const contributionSlider = page.locator('text=Taxa de Contribuição').locator('..').locator('input[type="range"]');
    if (await contributionSlider.isVisible()) {
      await contributionSlider.fill('0.08');
    }

    // Analisar resultados
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);

    // Verificar indicadores de suficiência
    await expect(page.locator('text=/Déficit|Superávit|Equilibrado/')).toBeVisible({ timeout: 10000 });

    // Verificar se gráficos são renderizados
    const charts = page.locator('canvas, svg, .recharts-wrapper');
    const chartsCount = await charts.count();
    expect(chartsCount).toBeGreaterThan(0);
  });

  test('sugestões inteligentes para BD', async ({ page }) => {
    // Configurar cenário com déficit
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('25'); // Idade jovem

    await page.click('text=Premissas');

    // Taxa de contribuição baixa
    const contributionSlider = page.locator('text=Taxa de Contribuição').locator('..').locator('input[type="range"]');
    if (await contributionSlider.isVisible()) {
      await contributionSlider.fill('0.05'); // 5% - muito baixo
    }

    // Verificar sugestões
    const suggestions = page.locator('text=Sugestões Inteligentes');
    if (await suggestions.isVisible()) {
      // Verificar se há sugestões disponíveis
      await expect(page.locator('button:has-text("Aplicar")')).toBeVisible({ timeout: 5000 });

      // Aplicar primeira sugestão
      const applyButton = page.locator('button:has-text("Aplicar")').first();
      if (await applyButton.isVisible()) {
        await applyButton.click();

        // Verificar se valores foram atualizados
        await page.waitForTimeout(2000);
        const newContribution = await contributionSlider.inputValue();
        expect(parseFloat(newContribution)).toBeGreaterThan(0.05);
      }
    }
  });

  test('exportar dados BD para análise', async ({ page }) => {
    // Configurar simulação básica
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('35');

    // Ir para resultados
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);

    // Verificar se dados estão disponíveis
    await expect(page.locator('text=/RMBA/')).toBeVisible({ timeout: 10000 });

    // Verificar premissas exibidas
    const assumptions = page.locator('text=Premissas da Simulação');
    if (await assumptions.isVisible()) {
      await expect(page.locator('text=/Idade|Gênero/')).toBeVisible();
      await expect(page.locator('text=/Salário/')).toBeVisible();
      await expect(page.locator('text=/Taxa|Desconto/')).toBeVisible();
    }
  });
});