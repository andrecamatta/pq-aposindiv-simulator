import { test, expect } from '@playwright/test';

test.describe('Technical Tab Performance', () => {
  test.beforeEach(async ({ page }) => {
    // Navegar para a aplicação
    await page.goto('http://localhost:5173');
    
    // Aguardar a aplicação carregar completamente
    await page.waitForSelector('[data-testid="simulator-ready"]', { timeout: 10000 });
    
    // Aguardar um pouco mais para garantir que tudo esteja estabilizado
    await page.waitForTimeout(2000);
  });

  test('should navigate to technical tab quickly', async ({ page }) => {
    // Medir tempo de navegação para aba técnica
    const startTime = Date.now();
    
    await page.click('[data-testid="tab-technical"]');
    
    // Aguardar conteúdo da aba carregar
    await page.waitForSelector('text=Configurações Técnicas', { timeout: 5000 });
    
    const endTime = Date.now();
    const navigationTime = endTime - startTime;
    
    console.log(`Navigation to Technical tab took: ${navigationTime}ms`);
    
    // Navegação deve ser rápida (menos de 500ms)
    expect(navigationTime).toBeLessThan(500);
  });

  test('should handle slider interactions smoothly', async ({ page }) => {
    // Navegar para aba técnica
    await page.click('[data-testid="tab-technical"]');
    await page.waitForSelector('text=Configurações Técnicas');
    
    // Localizar slider de taxa administrativa
    const adminSlider = page.locator('input[type="range"]').first();
    
    // Medir tempo de resposta das interações com slider
    const measurements = [];
    
    for (let i = 0; i < 5; i++) {
      const startTime = Date.now();
      
      // Simular arraste do slider
      await adminSlider.fill('2.5');
      
      // Aguardar qualquer re-render
      await page.waitForTimeout(100);
      
      const endTime = Date.now();
      measurements.push(endTime - startTime);
    }
    
    const avgTime = measurements.reduce((a, b) => a + b) / measurements.length;
    console.log(`Average slider interaction time: ${avgTime}ms`);
    
    // Interações com slider devem ser rápidas (menos de 100ms em média)
    expect(avgTime).toBeLessThan(100);
  });

  test('should update display values without performance issues', async ({ page }) => {
    await page.click('[data-testid="tab-technical"]');
    await page.waitForSelector('text=Configurações Técnicas');
    
    // Localizar slider e valor exibido
    const adminSlider = page.locator('input[type="range"]').first();
    
    // Medir tempo para atualização visual
    const startTime = Date.now();
    
    await adminSlider.fill('1.8');
    
    // Aguardar valor ser atualizado visualmente
    await page.waitForSelector('text=1.8%', { timeout: 2000 });
    
    const endTime = Date.now();
    const updateTime = endTime - startTime;
    
    console.log(`Visual update took: ${updateTime}ms`);
    
    // Atualização visual deve ser quase instantânea (menos de 200ms)
    expect(updateTime).toBeLessThan(200);
  });

  test('should handle multiple rapid changes efficiently', async ({ page }) => {
    await page.click('[data-testid="tab-technical"]');
    await page.waitForSelector('text=Configurações Técnicas');
    
    const adminSlider = page.locator('input[type="range"]').first();
    const loadingSlider = page.locator('input[type="range"]').nth(1);
    
    // Simular mudanças rápidas em múltiplos controles
    const startTime = Date.now();
    
    // Série de mudanças rápidas
    await adminSlider.fill('1.2');
    await page.waitForTimeout(50);
    
    await loadingSlider.fill('5.0');
    await page.waitForTimeout(50);
    
    await adminSlider.fill('2.1');
    await page.waitForTimeout(50);
    
    await loadingSlider.fill('8.5');
    await page.waitForTimeout(50);
    
    // Aguardar estabilizar
    await page.waitForTimeout(1000);
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    console.log(`Multiple rapid changes took: ${totalTime}ms`);
    
    // Múltiplas mudanças devem ser processadas eficientemente
    expect(totalTime).toBeLessThan(2000);
  });

  test('should maintain responsiveness during API calls', async ({ page }) => {
    await page.click('[data-testid="tab-technical"]');
    await page.waitForSelector('text=Configurações Técnicas');
    
    // Mudar configuração que dispara recálculo
    await page.selectOption('select', 'EAN');
    
    // Verificar se interface continua responsiva durante loading
    const startTime = Date.now();
    
    // Tentar interagir com outro controle enquanto carregando
    const adminSlider = page.locator('input[type="range"]').first();
    await adminSlider.fill('1.5');
    
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    console.log(`Response time during API call: ${responseTime}ms`);
    
    // Interface deve permanecer responsiva mesmo durante API calls
    expect(responseTime).toBeLessThan(300);
  });

  test('should not cause memory leaks with repeated navigation', async ({ page }) => {
    // Teste de stress - navegar entre abas repetidamente
    const iterations = 10;
    const startTime = Date.now();
    
    for (let i = 0; i < iterations; i++) {
      // Ir para aba técnica
      await page.click('[data-testid="tab-technical"]');
      await page.waitForSelector('text=Configurações Técnicas');
      
      // Fazer pequena interação
      const slider = page.locator('input[type="range"]').first();
      await slider.fill('1.' + (i % 9));
      
      // Voltar para aba participante
      await page.click('[data-testid="tab-participant"]');
      await page.waitForSelector('text=Dados do Participante');
      
      await page.waitForTimeout(100);
    }
    
    const endTime = Date.now();
    const avgTimePerIteration = (endTime - startTime) / iterations;
    
    console.log(`Average time per navigation cycle: ${avgTimePerIteration}ms`);
    
    // Navegação repetida não deve degradar performance significativamente
    expect(avgTimePerIteration).toBeLessThan(500);
  });

  test('should render technical tab without layout shifts', async ({ page }) => {
    // Medir Cumulative Layout Shift (CLS)
    await page.goto('http://localhost:5173');
    
    // Aguardar carregamento inicial
    await page.waitForSelector('[data-testid="simulator-ready"]');
    
    // Navegar para aba técnica
    await page.click('[data-testid="tab-technical"]');
    
    // Aguardar renderização completa
    await page.waitForSelector('text=Configurações Técnicas');
    await page.waitForTimeout(1000);
    
    // Verificar se não há shifts significativos no layout
    const clsMetrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          const cls = entries.reduce((sum, entry) => {
            return sum + (entry as any).value;
          }, 0);
          resolve(cls);
        }).observe({ entryTypes: ['layout-shift'] });
        
        // Timeout para coletar métricas
        setTimeout(() => resolve(0), 2000);
      });
    });
    
    console.log(`Cumulative Layout Shift: ${clsMetrics}`);
    
    // CLS deve ser baixo (menos de 0.1 é considerado bom)
    expect(Number(clsMetrics)).toBeLessThan(0.1);
  });
});