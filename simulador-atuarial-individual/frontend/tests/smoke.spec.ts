import { test, expect } from '@playwright/test';

test.describe('Smoke Tests - Funcionalidades Principais', () => {
  test.beforeEach(async ({ page }) => {
    // Navegar para aplicação
    await page.goto('http://localhost:5173');
  });

  test('app carrega sem erros', async ({ page }) => {
    // Verifica se título existe
    await expect(page).toHaveTitle(/Simulador/i);
    
    // Verifica se não há erros no console
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Aguarda carregamento completo
    await page.waitForLoadState('networkidle');
    
    // Não deve ter erros críticos
    expect(consoleErrors.filter(e => 
      !e.includes('WebSocket') && // Ignora avisos de WebSocket
      !e.includes('favicon')      // Ignora erro de favicon
    )).toHaveLength(0);
  });

  test('navegação entre abas funciona', async ({ page }) => {
    // Aguarda app carregar
    await page.waitForSelector('text=Participante', { timeout: 10000 });
    
    // Testa navegação para cada aba principal
    const tabs = [
      { name: 'Resultados', content: 'Análise' },
      { name: 'Sensibilidade', content: 'Sensibilidade' },
      { name: 'Premissas', content: 'Premissas' },
      { name: 'Técnico', content: 'Configurações Técnicas' }
    ];
    
    for (const tab of tabs) {
      // Clica na aba
      await page.click(`text=${tab.name}`);
      
      // Verifica se conteúdo da aba aparece
      await expect(page.locator(`text=${tab.content}`)).toBeVisible({ timeout: 5000 });
    }
    
    // Volta para aba inicial
    await page.click('text=Participante');
    await expect(page.locator('text=Dados do Participante')).toBeVisible();
  });

  test('formulário do participante aceita dados', async ({ page }) => {
    // Aguarda formulário carregar
    await page.waitForSelector('input[type="number"]');
    
    // Preenche idade
    const ageInput = page.locator('input[type="number"]').first();
    await ageInput.fill('35');
    await expect(ageInput).toHaveValue('35');
    
    // Seleciona gênero (se houver select)
    const genderSelect = page.locator('select').first();
    if (await genderSelect.isVisible()) {
      await genderSelect.selectOption({ index: 1 });
    }
    
    // Preenche salário
    const salaryInputs = page.locator('input[type="text"]');
    const salaryInput = salaryInputs.first();
    if (await salaryInput.isVisible()) {
      await salaryInput.fill('5000');
    }
  });

  test('sliders funcionam e atualizam valores', async ({ page }) => {
    // Navega para aba com sliders
    await page.click('text=Premissas');
    await page.waitForSelector('input[type="range"]', { timeout: 5000 });
    
    // Pega primeiro slider
    const slider = page.locator('input[type="range"]').first();
    
    // Pega valor inicial
    const initialValue = await slider.inputValue();
    
    // Move slider
    await slider.fill('15');
    
    // Verifica se valor mudou
    const newValue = await slider.inputValue();
    expect(newValue).not.toBe(initialValue);
    expect(newValue).toBe('15');
    
    // Verifica se display foi atualizado (procura por texto com o novo valor)
    await expect(page.locator('text=/15/')).toBeVisible({ timeout: 2000 });
  });

  test('cálculo é executado e resultados aparecem', async ({ page }) => {
    // Preenche dados mínimos
    await page.waitForSelector('input[type="number"]');
    
    // Define idade
    const ageInput = page.locator('input[type="number"]').first();
    await ageInput.fill('30');
    
    // Vai para aba de resultados
    await page.click('text=Resultados');
    
    // Aguarda algum resultado aparecer
    await page.waitForSelector('text=/R\\$|\\d+/', { timeout: 10000 });
    
    // Verifica se tem valores monetários
    const currencyValues = await page.locator('text=/R\\$\\s*[\\d.,]+/').count();
    expect(currencyValues).toBeGreaterThan(0);
  });

  test('gráficos são renderizados', async ({ page }) => {
    // Vai para aba de resultados
    await page.click('text=Resultados');
    
    // Aguarda gráficos carregarem (canvas ou svg)
    const charts = await page.locator('canvas, svg').count();
    expect(charts).toBeGreaterThan(0);
    
    // Verifica se Recharts está renderizando
    const rechartsElements = await page.locator('.recharts-wrapper').count();
    if (rechartsElements > 0) {
      // Verifica se tem elementos do gráfico
      await expect(page.locator('.recharts-surface')).toBeVisible({ timeout: 5000 });
    }
  });

  test('responsividade - layout não quebra', async ({ page }) => {
    // Testa em diferentes tamanhos
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      
      // Verifica se elementos principais estão visíveis
      await expect(page.locator('text=Simulador')).toBeVisible();
      
      // Verifica se não há overflow horizontal
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeLessThanOrEqual(viewport.width + 20); // Margem de tolerância
    }
  });

  test('tipo de plano pode ser alternado', async ({ page }) => {
    // Procura por seletor de tipo de plano
    const planTypeSelects = page.locator('select');
    
    for (let i = 0; i < await planTypeSelects.count(); i++) {
      const select = planTypeSelects.nth(i);
      const options = await select.locator('option').allTextContents();
      
      // Verifica se é o select de tipo de plano
      if (options.some(opt => opt.includes('BD') || opt.includes('CD'))) {
        // Tenta alternar
        await select.selectOption({ index: 1 });
        
        // Verifica se interface se adapta
        await page.waitForTimeout(500);
        
        // Não deve ter erros
        const hasError = await page.locator('text=/erro|error/i').isVisible();
        expect(hasError).toBe(false);
        break;
      }
    }
  });

  test('dados persistem ao navegar entre abas', async ({ page }) => {
    // Define um valor específico
    await page.waitForSelector('input[type="number"]');
    const ageInput = page.locator('input[type="number"]').first();
    await ageInput.fill('42');
    
    // Navega para outra aba
    await page.click('text=Resultados');
    await page.waitForTimeout(500);
    
    // Volta para aba original
    await page.click('text=Participante');
    
    // Verifica se valor persiste
    const ageValue = await page.locator('input[type="number"]').first().inputValue();
    expect(ageValue).toBe('42');
  });

  test('tooltips e ajuda estão disponíveis', async ({ page }) => {
    // Procura por ícones de informação
    const infoIcons = await page.locator('[class*="info"], [class*="help"], [title]').count();
    expect(infoIcons).toBeGreaterThan(0);
    
    // Testa hover em um elemento com tooltip
    const elementWithTooltip = page.locator('[title]').first();
    if (await elementWithTooltip.isVisible()) {
      await elementWithTooltip.hover();
      // Tooltip pode aparecer após hover
      await page.waitForTimeout(500);
    }
  });

  test('aba sensibilidade está acessível e funcional', async ({ page }) => {
    // Navega para aba de sensibilidade
    await page.click('text=Sensibilidade');
    
    // Verifica se o header principal da aba aparece (h2)
    await expect(page.locator('h2:has-text("Análise de Sensibilidade")')).toBeVisible({ timeout: 5000 });
    
    // Verifica se mostra mensagem para executar simulação quando não há dados
    const executeMessage = page.locator('text=/Execute.*Simulação/i');
    const sensitivityPlaceholder = page.locator('text=/Em breve/i, text=/CD/i');
    
    // Deve ter mensagem para executar simulação ou placeholder para CD
    const hasExecuteMessage = await executeMessage.isVisible();
    const hasPlaceholder = await sensitivityPlaceholder.count() > 0;
    
    expect(hasExecuteMessage || hasPlaceholder).toBe(true);
    
    // Verifica se não há erros JavaScript críticos
    const hasError = await page.locator('text=/erro|error/i').isVisible();
    expect(hasError).toBe(false);
  });
});

test.describe('Smoke Tests - Casos Críticos', () => {
  test('app não quebra com valores extremos', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForSelector('input[type="number"]');
    
    // Testa idade muito alta
    const ageInput = page.locator('input[type="number"]').first();
    await ageInput.fill('120');
    
    // Não deve ter erro
    await page.waitForTimeout(1000);
    const hasError = await page.locator('text=/erro|error/i').isVisible();
    expect(hasError).toBe(false);
    
    // Testa valor muito baixo
    await ageInput.fill('1');
    await page.waitForTimeout(1000);
    
    // App ainda deve estar funcionando
    await expect(page.locator('text=Simulador')).toBeVisible();
  });

  test('loading states funcionam corretamente', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Muda valor que dispara recálculo
    await page.waitForSelector('input[type="number"]');
    const input = page.locator('input[type="number"]').first();
    
    // Faz mudança rápida
    await input.fill('25');
    
    // Pode haver indicador de loading
    const loadingIndicator = page.locator('[class*="loading"], [class*="spinner"]');
    if (await loadingIndicator.isVisible()) {
      // Loading deve desaparecer eventualmente
      await expect(loadingIndicator).not.toBeVisible({ timeout: 5000 });
    }
  });

  test('mensagens de erro são exibidas adequadamente', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Tenta valor inválido
    const input = page.locator('input[type="number"]').first();
    if (await input.isVisible()) {
      await input.fill('-10');
      
      // Pode haver validação
      const errorMessage = page.locator('[class*="error"], [class*="invalid"]');
      // Se houver erro, deve ser visível
      if (await errorMessage.count() > 0) {
        await expect(errorMessage.first()).toBeVisible();
      }
    }
  });
});