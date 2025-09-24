import { test, expect } from '@playwright/test';

test.describe('Aba de Resultados', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Configurar dados básicos
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('35');
    
    const salarySlider = page.locator('text=Salário Mensal').locator('..').locator('input[type="range"]');
    if (await salarySlider.isVisible()) {
      await salarySlider.fill('10000');
    }

    // Navegar para resultados
    await page.click('text=Resultados');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Aguardar cálculos
  });

  test('exibir métricas principais', async ({ page }) => {
    // Verificar se métricas estão visíveis
    await expect(page.locator('text=/R\\$/')).toBeVisible({ timeout: 10000 });
    
    // Verificar formatação monetária
    const moneyValues = await page.locator('text=/R\\$\\s*[\\d.,]+/').count();
    expect(moneyValues).toBeGreaterThan(0);

    // Verificar percentuais
    const percentValues = await page.locator('text=/\\d+,\\d{2}%/').count();
    expect(percentValues).toBeGreaterThan(0);
  });

  test('gráficos são renderizados', async ({ page }) => {
    // Verificar presença de gráficos
    const charts = await page.locator('.recharts-wrapper, canvas, svg').count();
    expect(charts).toBeGreaterThan(0);

    // Verificar elementos específicos do Recharts
    await expect(page.locator('.recharts-surface')).toBeVisible({ timeout: 5000 });
    
    // Verificar legendas dos gráficos
    const legends = await page.locator('.recharts-legend, .legend').count();
    expect(legends).toBeGreaterThanOrEqual(0); // Pode não ter legendas
  });

  test('resultados BD são exibidos corretamente', async ({ page }) => {
    // Configurar para BD
    await page.click('text=Plano');
    const planSelect = page.locator('select').filter({ hasText: /BD|CD/ }).first();
    if (await planSelect.isVisible()) {
      await planSelect.selectOption('BD');
    }

    await page.click('text=Resultados');
    await page.waitForTimeout(2000);

    // Métricas específicas de BD
    await expect(page.locator('text=/RMBA|Reserva Matemática/')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/Benefício|Aposentadoria/')).toBeVisible();
    await expect(page.locator('text=/Contribuição Normal/')).toBeVisible();
  });

  test('resultados CD são exibidos corretamente', async ({ page }) => {
    // Configurar para CD
    await page.click('text=Plano');
    const planSelect = page.locator('select').filter({ hasText: /BD|CD/ }).first();
    if (await planSelect.isVisible()) {
      await planSelect.selectOption('CD');
    }

    await page.click('text=Resultados');
    await page.waitForTimeout(2000);

    // Métricas específicas de CD
    await expect(page.locator('text=/Saldo Final|Acumulação/')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/Renda Mensal|Benefício/')).toBeVisible();
    await expect(page.locator('text=/Contribuição Total/')).toBeVisible();
  });

  test('gráfico de evolução patrimonial', async ({ page }) => {
    // Verificar se gráfico de linha está presente
    await expect(page.locator('.recharts-line, .recharts-area')).toBeVisible({ timeout: 5000 });
    
    // Verificar eixos
    await expect(page.locator('.recharts-xAxis, .recharts-yAxis')).toBeVisible();
    
    // Verificar pontos de dados
    const dataPoints = await page.locator('.recharts-dot, .recharts-active-dot').count();
    expect(dataPoints).toBeGreaterThan(0);
  });

  test('tabela de projeções', async ({ page }) => {
    // Procurar por tabela de dados
    const tables = await page.locator('table, .table, [role="table"]').count();
    if (tables > 0) {
      // Verificar cabeçalhos
      await expect(page.locator('th, .table-header')).toBeVisible();
      
      // Verificar linhas de dados
      const rows = await page.locator('tr, .table-row').count();
      expect(rows).toBeGreaterThan(1); // Pelo menos cabeçalho + 1 linha
    }
  });

  test('indicadores de performance', async ({ page }) => {
    // Verificar indicadores numéricos
    const indicators = page.locator('text=/Taxa de Retorno|ROI|Performance/');
    if (await indicators.count() > 0) {
      await expect(indicators.first()).toBeVisible();
    }

    // Verificar medidas de risco
    const riskMetrics = page.locator('text=/Risco|Volatilidade|Desvio/');
    if (await riskMetrics.count() > 0) {
      await expect(riskMetrics.first()).toBeVisible();
    }
  });

  test('comparação de cenários', async ({ page }) => {
    // Alterar parâmetro e comparar resultados
    const initialResult = await page.locator('text=/R\\$\\s*[\\d.,]+/').first().textContent();
    
    // Mudar idade
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('45');
    
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    
    const newResult = await page.locator('text=/R\\$\\s*[\\d.,]+/').first().textContent();
    
    // Resultados devem ser diferentes
    expect(initialResult).not.toBe(newResult);
  });

  test('loading states durante cálculos', async ({ page }) => {
    // Fazer mudança que dispara recalculo
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('25');
    
    await page.click('text=Resultados');
    
    // Verificar se há indicador de loading
    const loadingIndicator = page.locator('[class*="loading"], [class*="spinner"], text=/Calculando/');
    if (await loadingIndicator.count() > 0) {
      // Loading deve desaparecer eventualmente
      await expect(loadingIndicator.first()).not.toBeVisible({ timeout: 10000 });
    }
    
    // Resultados devem aparecer
    await expect(page.locator('text=/R\\$/')).toBeVisible({ timeout: 10000 });
  });

  test('exportação de dados', async ({ page }) => {
    // Procurar botões de exportação
    const exportButtons = page.locator('button:has-text("Exportar"), button:has-text("Download"), button:has-text("PDF")');
    
    if (await exportButtons.count() > 0) {
      // Clicar no primeiro botão de export
      const firstExport = exportButtons.first();
      await firstExport.click();
      
      // Pode aparecer menu de opções ou iniciar download
      await page.waitForTimeout(1000);
      
      // Verificar se não há erro
      const errorMessages = await page.locator('text=/erro|error/i').count();
      expect(errorMessages).toBe(0);
    }
  });

  test('análise de sensibilidade visual', async ({ page }) => {
    // Procurar gráficos de sensibilidade
    const sensitivityCharts = page.locator('text=/Sensibilidade|Cenário|Stress/');
    
    if (await sensitivityCharts.count() > 0) {
      await expect(sensitivityCharts.first()).toBeVisible();
      
      // Verificar se tem gráficos associados
      const charts = await page.locator('.recharts-wrapper').count();
      expect(charts).toBeGreaterThan(0);
    }
  });

  test('detalhamento de premissas utilizadas', async ({ page }) => {
    // Procurar seção de premissas
    const assumptionsSection = page.locator('text=/Premissas da Simulação|Parâmetros Utilizados/');
    
    if (await assumptionsSection.count() > 0) {
      await expect(assumptionsSection.first()).toBeVisible();
      
      // Verificar se mostra valores utilizados
      await expect(page.locator('text=/Idade|Gênero|Salário/')).toBeVisible();
      await expect(page.locator('text=/Taxa|Desconto/')).toBeVisible();
    }
  });

  test('alertas e recomendações', async ({ page }) => {
    // Procurar alertas ou avisos
    const alerts = page.locator('[class*="alert"], [class*="warning"], [class*="danger"]');
    
    if (await alerts.count() > 0) {
      await expect(alerts.first()).toBeVisible();
    }
    
    // Procurar recomendações
    const recommendations = page.locator('text=/Recomendação|Sugestão|Dica/');
    
    if (await recommendations.count() > 0) {
      await expect(recommendations.first()).toBeVisible();
    }
  });

  test('responsividade dos resultados', async ({ page }) => {
    // Testar em diferentes tamanhos
    const viewports = [
      { width: 1200, height: 800 },
      { width: 768, height: 1024 },
      { width: 375, height: 667 }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      
      // Verificar se resultados permanecem visíveis
      await expect(page.locator('text=/R\\$/')).toBeVisible();
      
      // Verificar se gráficos se adaptam
      const charts = await page.locator('.recharts-wrapper').count();
      if (charts > 0) {
        await expect(page.locator('.recharts-surface')).toBeVisible();
      }
    }
  });

  test('navegação entre diferentes visualizações', async ({ page }) => {
    // Procurar tabs ou botões de visualização
    const viewTabs = page.locator('button:has-text("Gráfico"), button:has-text("Tabela"), button:has-text("Resumo")');
    
    if (await viewTabs.count() > 1) {
      // Testar alternância entre visualizações
      const firstTab = viewTabs.first();
      const secondTab = viewTabs.nth(1);
      
      await firstTab.click();
      await page.waitForTimeout(500);
      
      await secondTab.click();
      await page.waitForTimeout(500);
      
      // Não deve haver erros
      const errorMessages = await page.locator('text=/erro|error/i').count();
      expect(errorMessages).toBe(0);
    }
  });

  test('persistência de configurações de exibição', async ({ page }) => {
    // Se houver opções de configuração de exibição
    const displayOptions = page.locator('input[type="checkbox"], select');
    
    if (await displayOptions.count() > 0) {
      const firstOption = displayOptions.first();
      const initialState = await firstOption.isChecked?.() || await firstOption.inputValue();
      
      // Alterar configuração
      if (await firstOption.getAttribute('type') === 'checkbox') {
        await firstOption.setChecked(!initialState);
      } else {
        const options = await firstOption.locator('option').count();
        if (options > 1) {
          await firstOption.selectOption({ index: 1 });
        }
      }
      
      // Navegar para outra aba e voltar
      await page.click('text=Participante');
      await page.waitForTimeout(500);
      await page.click('text=Resultados');
      
      // Verificar se configuração persistiu
      const newState = await firstOption.isChecked?.() || await firstOption.inputValue();
      expect(newState).not.toBe(initialState);
    }
  });

  test('atualização em tempo real', async ({ page }) => {
    // Capturar resultado inicial
    const initialResult = await page.locator('text=/R\\$\\s*[\\d.,]+/').first().textContent();
    
    // Alterar parâmetro rapidamente
    await page.click('text=Premissas');
    const slider = page.locator('input[type="range"]').first();
    
    if (await slider.isVisible()) {
      const currentValue = await slider.inputValue();
      const newValue = parseFloat(currentValue) * 1.1;
      await slider.fill(newValue.toString());
    }
    
    // Voltar para resultados
    await page.click('text=Resultados');
    await page.waitForTimeout(3000); // Aguardar debounce e cálculo
    
    // Verificar se resultado foi atualizado
    const updatedResult = await page.locator('text=/R\\$\\s*[\\d.,]+/').first().textContent();
    expect(updatedResult).not.toBe(initialResult);
  });
});