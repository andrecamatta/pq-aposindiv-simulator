import { test, expect } from '@playwright/test';
import { navigateToTab, waitForCalculations, fillSliderWithValidation, waitForMonetaryValue } from './helpers/test-utils';

test.describe('Fluxo Completo CD (Contribuição Definida)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Configurar para plano CD
    await page.click('text=Plano');
    const planTypeSelect = page.locator('select').filter({ hasText: /BD|CD/ }).first();
    if (await planTypeSelect.isVisible()) {
      await planTypeSelect.selectOption('CD');
    }
  });

  test('configuração básica de plano CD', async ({ page }) => {
    // Verificar se interface CD está ativa
    await expect(page.locator('text=/Saldo Projetado|Contribuição Mensal/')).toBeVisible({ timeout: 5000 });

    // Configurar participante
    await page.click('text=Participante');
    const ageSlider = page.locator('input[type="range"]').first();
    const min = parseInt(await ageSlider.getAttribute('min') || '18');
    const max = parseInt(await ageSlider.getAttribute('max') || '75');
    const validAge = Math.min(max, Math.max(min, 30));
    await ageSlider.fill(validAge.toString());
    
    const salarySlider = page.locator('text=Salário Mensal').locator('..').locator('input[type="range"]');
    if (await salarySlider.isVisible()) {
      const min = parseInt(await salarySlider.getAttribute('min') || '1000');
      const max = parseInt(await salarySlider.getAttribute('max') || '100000');
      const validSalary = Math.min(max, Math.max(min, 8000));
      await salarySlider.fill(validSalary.toString());
    }

    // Configurar saldo inicial CD
    const balanceSlider = page.locator('text=Saldo Inicial').locator('..').locator('input[type="range"]');
    if (await balanceSlider.isVisible()) {
      const min = parseInt(await balanceSlider.getAttribute('min') || '0');
      const max = parseInt(await balanceSlider.getAttribute('max') || '1000000');
      const validBalance = Math.min(max, Math.max(min, 25000));

      await balanceSlider.fill(validBalance.toString());
      await page.waitForTimeout(500);

      // Verifica se valor foi atualizado (formato pode variar)
      await expect(page.locator('text=/R\\$|' + validBalance + '/')).toBeVisible({ timeout: 2000 });
    }

    // Verificar resultados CD
    await navigateToTab(page, 'Resultados');
    await waitForCalculations(page);

    // Verificar métricas específicas de CD
    await expect(page.locator('text=/Saldo Final|Contribuição Total/')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/Renda Vitalícia|Renda Temporária/')).toBeVisible();
  });

  test('diferentes modos de conversão CD', async ({ page }) => {
    // Navegar para configurações técnicas
    await page.click('text=Técnico');
    
    // Testar modo de conversão para renda vitalícia
    const conversionSelect = page.locator('select').filter({ hasText: /Vitalícia|Temporária|Programada/ });
    if (await conversionSelect.isVisible()) {
      // Teste com renda vitalícia
      await conversionSelect.selectOption('LIFE_ANNUITY');
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      await expect(page.locator('text=/Renda Vitalícia/')).toBeVisible();

      // Voltar e testar renda temporária
      await page.click('text=Técnico');
      await conversionSelect.selectOption('TERM_CERTAIN');
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      await expect(page.locator('text=/Renda Temporária/')).toBeVisible();
    }
  });

  test('análise de contribuição CD', async ({ page }) => {
    await page.click('text=Premissas');

    // Ajustar taxa de contribuição
    const contributionSlider = page.locator('text=Taxa de Contribuição').locator('..').locator('input[type="range"]');
    if (await contributionSlider.isVisible()) {
      // Teste com contribuição baixa
      const min = parseFloat(await contributionSlider.getAttribute('min') || '0.01');
      const max = parseFloat(await contributionSlider.getAttribute('max') || '0.30');
      const validRate = Math.min(max, Math.max(min, 0.06));

      await contributionSlider.fill(validRate.toString());
      await page.waitForTimeout(500);

      // Ver impacto nos resultados
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      const lowContribResult = await page.locator('text=/R\\$\\s*[\\d.,]+/').first().textContent();

      // Aumentar contribuição
      await page.click('text=Premissas');
      const higherRate = Math.min(max, Math.max(min, 0.15));
      await contributionSlider.fill(higherRate.toString());
      await page.waitForTimeout(500);

      // Ver novo impacto
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      const highContribResult = await page.locator('text=/R\\$\\s*[\\d.,]+/').first().textContent();

      // Verificar que valores mudaram
      expect(lowContribResult).not.toBe(highContribResult);
    }
  });

  test('projeção de saldo CD ao longo do tempo', async ({ page }) => {
    // Configurar cenário
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('35');

    await page.click('text=Premissas');
    const retirementSlider = page.locator('text=Idade de Aposentadoria').locator('..').locator('input[type="range"]');
    if (await retirementSlider.isVisible()) {
      await retirementSlider.fill('65');
    }

    // Verificar gráfico de projeção
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);

    // Procurar por gráfico de evolução
    const charts = page.locator('.recharts-wrapper, canvas');
    const chartsCount = await charts.count();
    expect(chartsCount).toBeGreaterThan(0);

    // Verificar se há legendas de projeção
    await expect(page.locator('text=/Evolução|Projeção|Saldo/')).toBeVisible({ timeout: 5000 });
  });

  test('comparação entre perfis de investimento CD', async ({ page }) => {
    await page.click('text=Premissas');

    // Testar com diferentes taxas de retorno
    const returnSlider = page.locator('text=Taxa de Retorno').locator('..').locator('input[type="range"]');
    if (await returnSlider.isVisible()) {
      // Perfil conservador
      await returnSlider.fill('0.04');
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      const conservativeResult = await page.locator('text=/Saldo Final/').locator('..').textContent();

      // Perfil moderado
      await page.click('text=Premissas');
      await returnSlider.fill('0.06');
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      const moderateResult = await page.locator('text=/Saldo Final/').locator('..').textContent();

      // Perfil agressivo
      await page.click('text=Premissas');
      await returnSlider.fill('0.08');
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      const aggressiveResult = await page.locator('text=/Saldo Final/').locator('..').textContent();

      // Verificar que resultados são diferentes
      expect(conservativeResult).not.toBe(moderateResult);
      expect(moderateResult).not.toBe(aggressiveResult);
    }
  });

  test('cálculo de benefício CD com diferentes idades', async ({ page }) => {
    // Teste com aposentadoria precoce
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('40');

    await page.click('text=Premissas');
    const retirementSlider = page.locator('text=Idade de Aposentadoria').locator('..').locator('input[type="range"]');
    if (await retirementSlider.isVisible()) {
      await retirementSlider.fill('55'); // Aposentadoria precoce
    }

    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    const earlyRetirement = await page.locator('text=/Benefício|Renda/').locator('..').textContent();

    // Teste com aposentadoria tardia
    await page.click('text=Premissas');
    await retirementSlider.fill('70'); // Aposentadoria tardia

    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    const lateRetirement = await page.locator('text=/Benefício|Renda/').locator('..').textContent();

    // Verificar que valores são diferentes
    expect(earlyRetirement).not.toBe(lateRetirement);
  });

  test('validação de limites CD', async ({ page }) => {
    await page.click('text=Participante');

    // Testar saldo inicial máximo
    const balanceSlider = page.locator('text=Saldo Inicial').locator('..').locator('input[type="range"]');
    if (await balanceSlider.isVisible()) {
      const maxValue = await balanceSlider.getAttribute('max');
      await balanceSlider.fill(maxValue || '1000000');
      
      // Verificar formatação de valor alto
      await expect(page.locator('text=/R\\$\\s*[\\d.,]+/')).toBeVisible();
    }

    // Testar contribuição máxima
    await page.click('text=Premissas');
    const contributionSlider = page.locator('text=Taxa de Contribuição').locator('..').locator('input[type="range"]');
    if (await contributionSlider.isVisible()) {
      await contributionSlider.fill('0.20'); // 20% - limite típico
      await expect(page.locator('text=20,00%')).toBeVisible();
    }

    // Verificar se cálculos funcionam com valores extremos
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    await expect(page.locator('text=/R\\$/')).toBeVisible();
    
    // Não deve haver mensagens de erro
    const errorMessages = await page.locator('text=/erro|error/i').count();
    expect(errorMessages).toBe(0);
  });

  test('portabilidade de saldo CD', async ({ page }) => {
    // Simular cenário de portabilidade
    await page.click('text=Participante');
    
    // Definir saldo inicial alto (simulando portabilidade)
    const balanceSlider = page.locator('text=Saldo Inicial').locator('..').locator('input[type="range"]');
    if (await balanceSlider.isVisible()) {
      await balanceSlider.fill('150000');
      await expect(page.locator('text=R$ 150.000,00')).toBeVisible();
    }

    // Idade mais avançada
    await page.locator('input[type="range"]').first().fill('45');

    // Verificar impacto nos resultados
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);

    // Deve mostrar projeção considerando saldo portado
    await expect(page.locator('text=/Saldo Inicial|Valor Portado/')).toBeVisible({ timeout: 5000 });
  });
});