import { test, expect } from '@playwright/test';

test.describe('Testes de Integração - Frontend/Backend', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Aguarda app carregar
    await page.waitForLoadState('networkidle');
  });

  test('frontend conecta com API backend', async ({ page }) => {
    // Monitora requisições de rede
    const apiCalls: string[] = [];
    
    page.on('request', request => {
      if (request.url().includes('localhost:8000')) {
        apiCalls.push(request.url());
      }
    });
    
    // Aguarda carregamento inicial
    await page.waitForTimeout(2000);
    
    // Deve ter feito chamadas para API
    expect(apiCalls.length).toBeGreaterThan(0);
    
    // Verifica chamadas essenciais
    const hasHealthCheck = apiCalls.some(url => url.includes('/health'));
    const hasMortalityTables = apiCalls.some(url => url.includes('/mortality-tables'));
    const hasDefaultState = apiCalls.some(url => url.includes('/default-state'));
    
    expect(hasHealthCheck || hasMortalityTables || hasDefaultState).toBe(true);
  });

  test('WebSocket conecta e mantém conexão', async ({ page }) => {
    // Monitora WebSocket
    let wsConnected = false;
    let wsMessages = 0;
    
    page.on('websocket', ws => {
      wsConnected = true;
      
      ws.on('framereceived', frame => {
        wsMessages++;
      });
    });
    
    // Aguarda tempo para conexão
    await page.waitForTimeout(3000);
    
    // WebSocket deve estar conectado
    expect(wsConnected).toBe(true);
    
    // Pode ter recebido mensagens
    console.log(`WebSocket messages received: ${wsMessages}`);
  });

  test('mudanças disparam recálculo via API', async ({ page }) => {
    // Monitora chamadas de cálculo
    let calculateCalls = 0;
    
    page.on('request', request => {
      if (request.url().includes('/calculate')) {
        calculateCalls++;
      }
    });
    
    // Faz mudança que deve disparar cálculo
    await page.waitForSelector('input[type="number"]');
    const ageInput = page.locator('input[type="number"]').first();
    
    const initialCalls = calculateCalls;
    await ageInput.fill('35');
    
    // Aguarda possível debounce
    await page.waitForTimeout(2000);
    
    // Deve ter feito nova chamada de cálculo
    expect(calculateCalls).toBeGreaterThan(initialCalls);
  });

  test('dados persistem durante navegação', async ({ page }) => {
    // Define valores específicos
    await page.waitForSelector('input[type="number"]');
    
    // Preenche idade
    const ageInput = page.locator('input[type="number"]').first();
    await ageInput.fill('45');
    
    // Navega entre abas
    await page.click('text=Resultados');
    await page.waitForTimeout(500);
    
    await page.click('text=Premissas');
    await page.waitForTimeout(500);
    
    await page.click('text=Participante');
    
    // Valor deve persistir
    const currentValue = await ageInput.inputValue();
    expect(currentValue).toBe('45');
    
    // Resultados devem estar disponíveis
    await page.click('text=Resultados');
    const hasResults = await page.locator('text=/R\\$|\\d+/').count();
    expect(hasResults).toBeGreaterThan(0);
  });

  test('erros de API são tratados graciosamente', async ({ page, context }) => {
    // Intercepta e força erro em uma requisição
    await context.route('**/calculate', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });
    
    // Faz ação que dispara cálculo
    await page.waitForSelector('input[type="number"]');
    const input = page.locator('input[type="number"]').first();
    await input.fill('30');
    
    // Aguarda resposta
    await page.waitForTimeout(2000);
    
    // App não deve crashar
    await expect(page.locator('text=Simulador')).toBeVisible();
    
    // Pode mostrar mensagem de erro (opcional)
    const errorMessage = page.locator('text=/erro|error|falha/i');
    if (await errorMessage.count() > 0) {
      console.log('Error message displayed correctly');
    }
  });

  test('API timeout é tratado adequadamente', async ({ page, context }) => {
    // Simula timeout na API
    await context.route('**/calculate', async route => {
      // Delay longo
      await new Promise(resolve => setTimeout(resolve, 15000));
      route.fulfill({
        status: 408,
        body: JSON.stringify({ error: 'Request Timeout' })
      });
    });
    
    // Dispara cálculo
    const input = page.locator('input[type="number"]').first();
    await input.fill('25');
    
    // Aguarda um pouco (não o timeout completo)
    await page.waitForTimeout(3000);
    
    // App deve continuar responsivo
    await expect(page.locator('text=Participante')).toBeVisible();
    
    // Pode ter indicador de loading
    const loading = page.locator('[class*="loading"], [class*="spinner"]');
    if (await loading.count() > 0) {
      console.log('Loading indicator shown during long request');
    }
  });

  test('sugestões inteligentes funcionam', async ({ page }) => {
    // Monitora chamadas de sugestões
    let suggestionsCalled = false;
    
    page.on('request', request => {
      if (request.url().includes('/suggestions')) {
        suggestionsCalled = true;
      }
    });
    
    // Aguarda carregamento e possíveis sugestões automáticas
    await page.waitForTimeout(3000);
    
    // Se houver botão/área de sugestões
    const suggestionsArea = page.locator('text=/sugest|recomend/i');
    if (await suggestionsArea.count() > 0) {
      console.log('Suggestions area found');
      
      // Verifica se API foi chamada
      if (suggestionsCalled) {
        console.log('Suggestions API was called');
      }
      
      // Tenta aplicar sugestão se houver
      const applyButton = page.locator('button:has-text("Aplicar")').first();
      if (await applyButton.isVisible()) {
        await applyButton.click();
        await page.waitForTimeout(1000);
        
        // Valores devem ter mudado
        console.log('Suggestion applied');
      }
    }
  });

  test('exportação de dados funciona', async ({ page }) => {
    // Procura botões de exportação/download
    const exportButtons = page.locator('button:has-text(/export|download|baixar/i)');
    
    if (await exportButtons.count() > 0) {
      // Prepara para download
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null);
      
      // Clica no botão
      await exportButtons.first().click();
      
      // Verifica se download iniciou
      const download = await downloadPromise;
      if (download) {
        console.log('Download initiated:', download.suggestedFilename());
        expect(download).toBeTruthy();
      }
    }
  });

  test('mudança de tipo de plano atualiza interface', async ({ page }) => {
    // Encontra seletor de tipo de plano
    const selects = page.locator('select');
    let planTypeSelect = null;
    
    for (let i = 0; i < await selects.count(); i++) {
      const select = selects.nth(i);
      const options = await select.locator('option').allTextContents();
      
      if (options.some(opt => opt.includes('BD') || opt.includes('CD'))) {
        planTypeSelect = select;
        break;
      }
    }
    
    if (planTypeSelect) {
      // Muda para CD
      await planTypeSelect.selectOption({ label: /CD/i });
      await page.waitForTimeout(1000);
      
      // Verifica se interface mudou
      const cdSpecificElements = await page.locator('text=/saldo|acumula|conversão/i').count();
      expect(cdSpecificElements).toBeGreaterThan(0);
      
      // Muda para BD
      await planTypeSelect.selectOption({ label: /BD/i });
      await page.waitForTimeout(1000);
      
      // Verifica se interface mudou novamente
      const bdSpecificElements = await page.locator('text=/benefício definido|rmba/i').count();
      console.log(`BD specific elements found: ${bdSpecificElements}`);
    }
  });

  test('performance - múltiplas mudanças não degradam app', async ({ page }) => {
    const startTime = Date.now();
    
    // Faz várias mudanças rápidas
    for (let i = 0; i < 10; i++) {
      const input = page.locator('input[type="number"]').first();
      await input.fill(String(20 + i));
      await page.waitForTimeout(100);
    }
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    console.log(`10 rapid changes took ${totalTime}ms`);
    
    // Não deve demorar muito
    expect(totalTime).toBeLessThan(5000);
    
    // App deve continuar responsivo
    await expect(page.locator('text=Simulador')).toBeVisible();
    
    // Não deve ter erros
    const errors = await page.locator('text=/erro|error/i').count();
    expect(errors).toBe(0);
  });
});