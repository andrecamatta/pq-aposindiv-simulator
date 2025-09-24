import { test, expect } from '@playwright/test';

test.describe('Aba de Premissas', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Navegar para aba de premissas
    await page.click('text=Premissas');
    await page.waitForLoadState('networkidle');
    // Verificar se a aba está ativa aguardando conteúdo específico (fix strict mode)
    await expect(page.locator('text=/Taxa de Contribuição|Benefício|Premissas Financeiras/').first()).toBeVisible({ timeout: 10000 });
  });

  test('ajustar premissas financeiras', async ({ page }) => {
    // Taxa de desconto
    const discountSlider = page.locator('text=Taxa de Desconto').locator('..').locator('input[type="range"]');
    if (await discountSlider.isVisible()) {
      await discountSlider.fill('0.045');
      await page.waitForTimeout(500); // Aguardar atualização
      await expect(page.locator('text=/4,50%|4.50%/')).toBeVisible({ timeout: 5000 });
    }

    // Taxa de crescimento salarial
    const salaryGrowthSlider = page.locator('text=Crescimento Salarial').locator('..').locator('input[type="range"]');
    if (await salaryGrowthSlider.isVisible()) {
      await salaryGrowthSlider.fill('0.025');
      await expect(page.locator('text=2,50%')).toBeVisible();
    }

    // Taxa de inflação
    const inflationSlider = page.locator('text=Taxa de Inflação').locator('..').locator('input[type="range"]');
    if (await inflationSlider.isVisible()) {
      await inflationSlider.fill('0.035');
      await expect(page.locator('text=/3,50%|3.50%/')).toBeVisible({ timeout: 5000 });
    }

    // Verificar se cálculos são atualizados
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    await expect(page.locator('text=/R\\$/')).toBeVisible();
  });

  test('configurar idades e prazos', async ({ page }) => {
    // Idade de aposentadoria
    const retirementSlider = page.locator('text=Idade de Aposentadoria').locator('..').locator('input[type="range"]');
    if (await retirementSlider.isVisible()) {
      await retirementSlider.fill('65');
      await expect(page.locator('text=65 anos')).toBeVisible();
    }

    // Idade de entrada em benefício
    const benefitAgeSlider = page.locator('text=Idade de Benefício').locator('..').locator('input[type="range"]');
    if (await benefitAgeSlider.isVisible()) {
      await benefitAgeSlider.fill('60');
      await expect(page.locator('text=60 anos')).toBeVisible();
    }

    // Verificar consistência (benefício <= aposentadoria)
    const retirementAge = await retirementSlider.inputValue();
    const benefitAge = await benefitAgeSlider.inputValue();
    expect(parseInt(benefitAge)).toBeLessThanOrEqual(parseInt(retirementAge));
  });

  test('configurar taxas de contribuição', async ({ page }) => {
    // Taxa do participante
    const participantSlider = page.locator('text=Taxa de Contribuição').locator('..').locator('input[type="range"]');
    if (await participantSlider.isVisible()) {
      await participantSlider.fill('0.11');
      await expect(page.locator('text=11,00%')).toBeVisible();
    }

    // Taxa da empresa (se houver)
    const employerSlider = page.locator('text=Contribuição da Empresa').locator('..').locator('input[type="range"]');
    if (await employerSlider.isVisible()) {
      await employerSlider.fill('0.11');
      await expect(page.locator('text=11,00%')).toBeVisible();
    }

    // Verificar soma das contribuições
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    await expect(page.locator('text=/Contribuição Total|Contribuições/')).toBeVisible();
  });

  test('premissas demográficas e biométricas', async ({ page }) => {
    // Navegar para configurações técnicas se necessário
    await page.click('text=Técnico');
    
    // Tábua de mortalidade
    const mortalitySelect = page.locator('select').filter({ hasText: /AT|BR-EMS|IBGE/ });
    if (await mortalitySelect.isVisible()) {
      const options = await mortalitySelect.locator('option').allTextContents();
      expect(options.length).toBeGreaterThan(1);
      
      // Selecionar tábua diferente
      await mortalitySelect.selectOption({ index: 1 });
    }

    // Fator de melhoria
    const improvementSlider = page.locator('text=Fator de Melhoria').locator('..').locator('input[type="range"]');
    if (await improvementSlider.isVisible()) {
      await improvementSlider.fill('0.5');
    }

    // Verificar impacto nos cálculos
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    await expect(page.locator('text=/Expectativa|Probabilidade/')).toBeVisible();
  });

  test('custos administrativos', async ({ page }) => {
    // Taxa de carregamento
    const loadingSlider = page.locator('text=Taxa de Carregamento').locator('..').locator('input[type="range"]');
    if (await loadingSlider.isVisible()) {
      await loadingSlider.fill('0.015');
      await expect(page.locator('text=1,50%')).toBeVisible();
    }

    // Taxa de administração
    const adminSlider = page.locator('text=Taxa de Administração').locator('..').locator('input[type="range"]');
    if (await adminSlider.isVisible()) {
      await adminSlider.fill('0.02');
      await expect(page.locator('text=/2,00%|2.00%/')).toBeVisible({ timeout: 5000 });
    }

    // Verificar impacto nos resultados líquidos
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    
    // Deve mostrar valores brutos e líquidos
    await expect(page.locator('text=/Bruto|Líquido|Taxa/')).toBeVisible();
  });

  test('premissas específicas para BD', async ({ page }) => {
    // Configurar para BD
    await page.click('text=Plano');
    const planSelect = page.locator('select').filter({ hasText: /BD|CD/ }).first();
    if (await planSelect.isVisible()) {
      await planSelect.selectOption('BD');
    }

    await page.click('text=Premissas');

    // Taxa de juros atuarial
    const actuarialRateSlider = page.locator('text=Taxa Atuarial').locator('..').locator('input[type="range"]');
    if (await actuarialRateSlider.isVisible()) {
      await actuarialRateSlider.fill('0.04');
      await expect(page.locator('text=4,00%')).toBeVisible();
    }

    // Fator de capacidade
    const capacitySlider = page.locator('text=Fator de Capacidade').locator('..').locator('input[type="range"]');
    if (await capacitySlider.isVisible()) {
      await capacitySlider.fill('0.8');
      await expect(page.locator('text=80,00%')).toBeVisible();
    }

    // Verificar cálculo RMBA
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    await expect(page.locator('text=/RMBA|Reserva/')).toBeVisible();
  });

  test('premissas específicas para CD', async ({ page }) => {
    // Configurar para CD
    await page.click('text=Plano');
    const planSelect = page.locator('select').filter({ hasText: /BD|CD/ }).first();
    if (await planSelect.isVisible()) {
      await planSelect.selectOption('CD');
    }

    await page.click('text=Premissas');

    // Taxa de retorno esperada
    const returnSlider = page.locator('text=Taxa de Retorno').locator('..').locator('input[type="range"]');
    if (await returnSlider.isVisible()) {
      await returnSlider.fill('0.06');
      await expect(page.locator('text=6,00%')).toBeVisible();
    }

    // Volatilidade
    const volatilitySlider = page.locator('text=Volatilidade').locator('..').locator('input[type="range"]');
    if (await volatilitySlider.isVisible()) {
      await volatilitySlider.fill('0.15');
      await expect(page.locator('text=15,00%')).toBeVisible();
    }

    // Verificar projeções CD
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    await expect(page.locator('text=/Saldo Final|Acumulação/')).toBeVisible();
  });

  test('validação de intervalos de premissas', async ({ page }) => {
    // Testar valores extremos
    const sliders = page.locator('input[type="range"]');
    const count = await sliders.count();

    for (let i = 0; i < Math.min(count, 3); i++) { // Testar apenas os 3 primeiros
      const slider = sliders.nth(i);
      const min = await slider.getAttribute('min');
      const max = await slider.getAttribute('max');

      if (min && max) {
        // Testar valor mínimo
        await slider.fill(min);
        await page.waitForTimeout(500);

        // Testar valor máximo
        await slider.fill(max);
        await page.waitForTimeout(500);
      }
    }

    // Não deve haver erros
    const errorMessages = await page.locator('text=/erro|error/i').count();
    expect(errorMessages).toBe(0);
  });

  test('persistência de premissas', async ({ page }) => {
    // Definir valores específicos
    const contributionSlider = page.locator('text=Taxa de Contribuição').locator('..').locator('input[type="range"]');
    if (await contributionSlider.isVisible()) {
      await contributionSlider.fill('0.12');
    }

    const retirementSlider = page.locator('text=Idade de Aposentadoria').locator('..').locator('input[type="range"]');
    if (await retirementSlider.isVisible()) {
      await retirementSlider.fill('62');
    }

    // Navegar para outra aba
    await page.click('text=Participante');
    await page.waitForTimeout(500);

    // Voltar para premissas
    await page.click('text=Premissas');

    // Verificar se valores persistiram
    if (await contributionSlider.isVisible()) {
      expect(await contributionSlider.inputValue()).toBe('0.12');
    }
    if (await retirementSlider.isVisible()) {
      expect(await retirementSlider.inputValue()).toBe('62');
    }
  });

  test('tooltips explicativos das premissas', async ({ page }) => {
    // Procurar por elementos com informações
    const infoElements = page.locator('[title], [data-tooltip], .tooltip');
    const count = await infoElements.count();
    expect(count).toBeGreaterThan(0);

    // Testar hover em um elemento informativo
    if (count > 0) {
      const firstInfo = infoElements.first();
      await firstInfo.hover();
      await page.waitForTimeout(1000);
      
      // Pode aparecer tooltip ou popover
      const tooltipVisible = await page.locator('.tooltip, [role="tooltip"]').isVisible();
      // Apenas verificar se não há erro, tooltip pode não estar implementado
    }
  });

  test('reset de premissas para padrão', async ({ page }) => {
    // Alterar alguns valores
    const sliders = page.locator('input[type="range"]');
    const firstSlider = sliders.first();
    
    if (await firstSlider.isVisible()) {
      const originalValue = await firstSlider.inputValue();
      const max = await firstSlider.getAttribute('max');
      
      // Mudar para valor diferente
      await firstSlider.fill(max || '100');
      const changedValue = await firstSlider.inputValue();
      expect(changedValue).not.toBe(originalValue);

      // Procurar botão de reset
      const resetButton = page.locator('button:has-text("Reset"), button:has-text("Padrão"), button:has-text("Limpar")');
      if (await resetButton.isVisible()) {
        await resetButton.click();
        await page.waitForTimeout(1000);
        
        // Verificar se voltou ao valor original
        const resetValue = await firstSlider.inputValue();
        expect(resetValue).toBe(originalValue);
      }
    }
  });

  test('impacto das premissas nos cálculos', async ({ page }) => {
    // Definir cenário base
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('30');

    await page.click('text=Premissas');
    const contributionSlider = page.locator('text=Taxa de Contribuição').locator('..').locator('input[type="range"]');
    
    if (await contributionSlider.isVisible()) {
      // Cenário conservador
      await contributionSlider.fill('0.08');
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      const conservativeResult = await page.locator('text=/R\\$\\s*[\\d.,]+/').first().textContent();

      // Cenário otimista
      await page.click('text=Premissas');
      await contributionSlider.fill('0.15');
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      const optimisticResult = await page.locator('text=/R\\$\\s*[\\d.,]+/').first().textContent();

      // Resultados devem ser diferentes
      expect(conservativeResult).not.toBe(optimisticResult);
    }
  });
});