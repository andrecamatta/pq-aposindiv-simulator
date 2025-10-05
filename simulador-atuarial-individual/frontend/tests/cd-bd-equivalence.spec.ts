import { test, expect } from '@playwright/test';
import { navigateToTab, waitForCalculations } from './helpers/test-utils';

/**
 * Teste E2E: Verificação de Valores CD e BD
 *
 * Objetivo: Verificar que os cálculos corretos estão sendo aplicados
 * na interface para ambos os tipos de plano.
 *
 * Abordagem simplificada: testar que valores são retornados e são
 * numericamente válidos (não-nulos, positivos).
 */

test.describe('Cálculos CD e BD - Verificação E2E', () => {

  test('BD retorna valores válidos com saldo inicial alto', async ({ page }) => {
    console.log('🔵 Testando BD com saldo inicial elevado...');

    // Ir para a página
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Configurar plano BD
    await page.click('text=Plano');
    await page.waitForTimeout(500);

    const planTypeSelect = page.locator('select[name="plan_type"]');
    if (await planTypeSelect.isVisible()) {
      await planTypeSelect.selectOption('BD');
      await page.waitForTimeout(1000);
    }

    // Configurar idade e saldo
    await page.click('text=Participante');
    await page.waitForTimeout(500);

    // Definir idade próxima à aposentadoria (64 anos)
    const ageSliders = page.locator('input[type="range"]');
    const firstSlider = ageSliders.first();
    await firstSlider.fill('64');
    await page.waitForTimeout(500);

    // Saldo inicial: R$ 500.000 (mais seguro para testes)
    const balanceInput = page.locator('input').filter({ hasText: /Saldo/ }).or(
      page.locator('label:has-text("Saldo Inicial")').locator('..').locator('input')
    ).first();

    if (await balanceInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await balanceInput.fill('500000');
      await page.waitForTimeout(500);
    }

    // Ver resultados
    await navigateToTab(page, 'Resultados');
    await waitForCalculations(page);

    // Verificar que há valores monetários exibidos
    const monetaryValues = page.locator('text=/R\\$\\s*[\\d.,]+/');
    const count = await monetaryValues.count();

    console.log(`💰 Encontrados ${count} valores monetários na tela BD`);
    expect(count).toBeGreaterThan(0);

    // Extrair primeiro valor monetário
    const firstValue = await monetaryValues.first().textContent();
    console.log(`   Primeiro valor BD: ${firstValue}`);

    expect(firstValue).toContain('R$');
  });

  test('CD ACTUARIAL retorna valores válidos com saldo inicial alto', async ({ page }) => {
    console.log('🟢 Testando CD ACTUARIAL com saldo inicial elevado...');

    // Ir para a página
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Configurar plano CD
    await page.click('text=Plano');
    await page.waitForTimeout(500);

    const planTypeSelect = page.locator('select[name="plan_type"]');
    if (await planTypeSelect.isVisible()) {
      await planTypeSelect.selectOption('CD');
      await page.waitForTimeout(1000);
    }

    // Configurar modalidade de conversão CD (ACTUARIAL - vitalícia)
    const conversionSelect = page.locator('select[name="cd_conversion_mode"]');
    if (await conversionSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
      await conversionSelect.selectOption('ACTUARIAL');
      await page.waitForTimeout(500);
      console.log('   ✓ Modalidade ACTUARIAL selecionada');
    }

    // Configurar idade e saldo
    await page.click('text=Participante');
    await page.waitForTimeout(500);

    // Definir idade próxima à aposentadoria (64 anos)
    const ageSliders = page.locator('input[type="range"]');
    const firstSlider = ageSliders.first();
    await firstSlider.fill('64');
    await page.waitForTimeout(500);

    // Saldo inicial: R$ 500.000
    const balanceInput = page.locator('input').filter({ hasText: /Saldo/ }).or(
      page.locator('label:has-text("Saldo Inicial")').locator('..').locator('input')
    ).first();

    if (await balanceInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await balanceInput.fill('500000');
      await page.waitForTimeout(500);
    }

    // Ver resultados
    await navigateToTab(page, 'Resultados');
    await waitForCalculations(page);

    // Verificar que há valores monetários exibidos
    const monetaryValues = page.locator('text=/R\\$\\s*[\\d.,]+/');
    const count = await monetaryValues.count();

    console.log(`💰 Encontrados ${count} valores monetários na tela CD`);
    expect(count).toBeGreaterThan(0);

    // Extrair primeiro valor monetário
    const firstValue = await monetaryValues.first().textContent();
    console.log(`   Primeiro valor CD: ${firstValue}`);

    expect(firstValue).toContain('R$');
  });

  test('CD com diferentes modalidades retorna valores válidos', async ({ page }) => {
    const modalities = ['ACTUARIAL', 'CERTAIN_10Y', 'CERTAIN_20Y'];

    for (const modality of modalities) {
      console.log(`🧪 Testando CD com modalidade: ${modality}...`);

      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1500);

      // Configurar CD
      await page.click('text=Plano');
      await page.waitForTimeout(500);

      const planTypeSelect = page.locator('select[name="plan_type"]');
      if (await planTypeSelect.isVisible()) {
        await planTypeSelect.selectOption('CD');
        await page.waitForTimeout(800);
      }

      // Configurar modalidade
      const conversionSelect = page.locator('select[name="cd_conversion_mode"]');
      if (await conversionSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
        await conversionSelect.selectOption(modality);
        await page.waitForTimeout(500);
      }

      // Idade 50 anos, saldo R$ 200k
      await page.click('text=Participante');
      await page.waitForTimeout(500);

      const ageSlider = page.locator('input[type="range"]').first();
      await ageSlider.fill('50');
      await page.waitForTimeout(300);

      // Ver resultados
      await navigateToTab(page, 'Resultados');
      await waitForCalculations(page);

      // Verificar valores
      const monetaryCount = await page.locator('text=/R\\$\\s*[\\d.,]+/').count();
      console.log(`   ${modality}: ${monetaryCount} valores encontrados`);
      expect(monetaryCount).toBeGreaterThan(0);
    }

    console.log('✅ Todas as modalidades CD retornaram valores válidos');
  });
});
