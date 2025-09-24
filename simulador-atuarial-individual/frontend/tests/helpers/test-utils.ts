import { Page, expect } from '@playwright/test';

/**
 * Navegação segura entre abas com waits apropriados
 */
export async function navigateToTab(page: Page, tabName: string) {
  await page.click(`text=${tabName}`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500); // Aguarda transição

  // Verifica se a aba está ativa
  const isActive = await page.locator(`[aria-selected="true"]:has-text("${tabName}"), .active:has-text("${tabName}"), .tab-active:has-text("${tabName}")`).isVisible().catch(() => false);

  if (!isActive) {
    // Tenta clicar novamente se não estiver ativa
    await page.click(`text=${tabName}`);
    await page.waitForTimeout(500);
  }
}

/**
 * Aguarda cálculos serem processados
 */
export async function waitForCalculations(page: Page) {
  // Aguarda indicador de loading desaparecer
  const loadingIndicator = page.locator('[class*="loading"], [class*="spinner"], [class*="calculating"]');
  if (await loadingIndicator.isVisible().catch(() => false)) {
    await loadingIndicator.waitFor({ state: 'hidden', timeout: 30000 });
  }

  // Aguarda rede ficar idle
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000); // Buffer adicional
}

/**
 * Preenche slider com validação dinâmica
 */
export async function fillSliderWithValidation(page: Page, sliderLocator: any, desiredValue: number | string) {
  const slider = typeof sliderLocator === 'string' ? page.locator(sliderLocator) : sliderLocator;

  if (!await slider.isVisible()) {
    return false;
  }

  const min = parseFloat(await slider.getAttribute('min') || '0');
  const max = parseFloat(await slider.getAttribute('max') || '100');
  const step = parseFloat(await slider.getAttribute('step') || '1');

  let value = typeof desiredValue === 'string' ? parseFloat(desiredValue) : desiredValue;

  // Valida e ajusta o valor
  value = Math.max(min, Math.min(max, value));

  // Ajusta para o step mais próximo
  const steps = Math.round((value - min) / step);
  value = min + (steps * step);

  await slider.fill(value.toString());
  await page.waitForTimeout(500); // Aguarda atualização

  return true;
}

/**
 * Verifica se elemento está visível com retry
 */
export async function isElementVisible(page: Page, selector: string, options = { timeout: 5000, retries: 3 }) {
  for (let i = 0; i < options.retries; i++) {
    try {
      const element = page.locator(selector).first();
      await element.waitFor({ state: 'visible', timeout: options.timeout });
      return true;
    } catch {
      if (i < options.retries - 1) {
        await page.waitForTimeout(1000);
      }
    }
  }
  return false;
}

/**
 * Aguarda valor monetário aparecer
 */
export async function waitForMonetaryValue(page: Page, timeout = 10000) {
  await expect(page.locator('text=/R\\$\\s*[\\d.,]+/').first()).toBeVisible({ timeout });
}

/**
 * Aguarda gráficos carregarem
 */
export async function waitForCharts(page: Page, timeout = 15000) {
  const chartSelectors = [
    '.recharts-wrapper',
    'canvas',
    'svg.chart',
    '[class*="chart"]'
  ];

  for (const selector of chartSelectors) {
    const elements = await page.locator(selector).count();
    if (elements > 0) {
      await page.locator(selector).first().waitFor({ state: 'visible', timeout });
      return true;
    }
  }

  return false;
}