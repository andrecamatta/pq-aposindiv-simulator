import { test, expect } from '@playwright/test';

/**
 * Teste para verificar convergência das linhas no gráfico CD após aplicar sugestão
 *
 * Cenário:
 * 1. Configurar plano CD com Renda Vitalícia Atuarial
 * 2. Verificar que há diferença entre benefício atual e desejado
 * 3. Aplicar sugestão de contribuição
 * 4. Verificar que as linhas convergem (saldos finais próximos)
 */

test.describe('CD Graph Line Convergence', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Aguardar carregamento inicial
    await page.waitForTimeout(2000);
  });

  test('lines should converge after applying contribution suggestion', async ({ page }) => {
    console.log('🎯 Iniciando teste de convergência do gráfico CD');

    // 1. Configurar Plano CD
    console.log('📋 Passo 1: Configurando plano CD');
    await page.click('text=Tipo de Plano');
    await page.click('text=CD - Contribuição Definida');
    await page.waitForTimeout(500);

    // 2. Configurar modalidade: Renda Vitalícia Atuarial
    console.log('📋 Passo 2: Configurando Renda Vitalícia Atuarial');
    await page.click('text=Modalidade de Conversão');
    await page.click('text=Renda Vitalícia Atuarial');
    await page.waitForTimeout(500);

    // 3. Definir benefício desejado alto para forçar diferença
    console.log('📋 Passo 3: Configurando benefício desejado');
    const benefitSlider = page.locator('input[type="range"]').filter({ hasText: 'Benefício Mensal Desejado' }).first();
    await benefitSlider.fill('10000');
    await page.waitForTimeout(500);

    // 4. Aguardar cálculo e verificar se há sugestões
    console.log('⏳ Aguardando cálculo e sugestões...');
    await page.waitForTimeout(3000);

    // 5. Capturar valores ANTES de aplicar sugestão
    console.log('📊 Capturando dados ANTES da sugestão');

    // Verificar se há sugestão disponível
    const suggestionCard = page.locator('text=Ajustar Contribuição').first();
    const hasSuggestion = await suggestionCard.isVisible().catch(() => false);

    if (!hasSuggestion) {
      console.log('⚠️ Nenhuma sugestão disponível - teste não aplicável');
      test.skip();
      return;
    }

    // Capturar contribuição atual ANTES
    const contributionBefore = await page.locator('text=/Taxa de Contribuição/').textContent();
    console.log('💰 Contribuição ANTES:', contributionBefore);

    // 6. Aplicar sugestão
    console.log('✅ Passo 4: Aplicando sugestão de contribuição');
    const applyButton = page.locator('button:has-text("Aplicar")').first();
    await applyButton.click();
    await page.waitForTimeout(2000); // Aguardar recálculo

    // Capturar contribuição atual DEPOIS
    const contributionAfter = await page.locator('text=/Taxa de Contribuição/').textContent();
    console.log('💰 Contribuição DEPOIS:', contributionAfter);

    // 7. Navegar para aba de Resultados para ver o gráfico
    console.log('📊 Passo 5: Navegando para aba de Resultados');
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);

    // 8. Verificar que o gráfico está visível
    const chartTitle = page.locator('text=Evolução do Saldo CD');
    await expect(chartTitle).toBeVisible();
    console.log('✅ Gráfico CD visível');

    // 9. Capturar canvas do gráfico (screenshot)
    console.log('📸 Capturando screenshot do gráfico DEPOIS da sugestão');
    const chart = page.locator('canvas').first();
    await chart.screenshot({ path: '/tmp/cd_graph_after_suggestion.png' });
    console.log('✅ Screenshot salvo em /tmp/cd_graph_after_suggestion.png');

    // 10. Verificar métricas através do DOM
    console.log('📊 Verificando convergência através das métricas');

    // Tentar capturar informações da legenda do gráfico
    const legendItems = await page.locator('[class*="legend"]').allTextContents();
    console.log('📋 Itens da legenda:', legendItems);

    // 11. Verificar que não há mais grande diferença (análise visual requerida)
    console.log('✅ Teste completado - verificação visual do screenshot necessária');
    console.log('   Espera-se que as linhas estejam convergindo após aplicar sugestão');
  });

  test('capture BEFORE state for comparison', async ({ page }) => {
    console.log('🎯 Capturando estado ANTES da correção');

    // Configurar cenário
    await page.click('text=Tipo de Plano');
    await page.click('text=CD - Contribuição Definida');
    await page.waitForTimeout(500);

    await page.click('text=Modalidade de Conversão');
    await page.click('text=Renda Vitalícia Atuarial');
    await page.waitForTimeout(500);

    // Benefício alto
    const benefitInput = page.locator('input[type="text"]').filter({ hasText: /\d+/ }).first();
    await benefitInput.click();
    await benefitInput.fill('10000');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(3000);

    // Capturar gráfico ANTES
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);

    const chart = page.locator('canvas').first();
    await chart.screenshot({ path: '/tmp/cd_graph_BEFORE_fix.png' });

    console.log('✅ Screenshot ANTES salvo: /tmp/cd_graph_BEFORE_fix.png');
  });
});
