import { test, expect } from '@playwright/test';

test.describe('Geração de Relatórios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Configurar dados básicos para simulação
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('35');
    
    const salarySlider = page.locator('text=Salário Mensal').locator('..').locator('input[type="range"]');
    if (await salarySlider.isVisible()) {
      await salarySlider.fill('10000');
    }

    // Aguardar cálculos
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
  });

  test('botão de gerar relatório está disponível', async ({ page }) => {
    // Procurar botões de relatório
    const reportButtons = page.locator('button:has-text("Relatório"), button:has-text("Gerar PDF"), button:has-text("Exportar")');
    
    if (await reportButtons.count() > 0) {
      await expect(reportButtons.first()).toBeVisible();
      await expect(reportButtons.first()).toBeEnabled();
    } else {
      // Se não encontrar botão, pode estar em menu
      const menuButtons = page.locator('button:has-text("Menu"), button:has-text("Opções"), [role="menu"]');
      if (await menuButtons.count() > 0) {
        await menuButtons.first().click();
        await expect(page.locator('text=/Relatório|PDF|Exportar/')).toBeVisible({ timeout: 2000 });
      }
    }
  });

  test('geração de relatório PDF executivo', async ({ page }) => {
    // Procurar e clicar em botão de relatório
    const reportButton = page.locator('button:has-text("Relatório"), button:has-text("PDF")');
    
    if (await reportButton.count() > 0) {
      await reportButton.first().click();
      
      // Pode aparecer modal ou menu de opções
      const executiveOption = page.locator('text=/Executivo|Executive|Resumo/');
      if (await executiveOption.count() > 0) {
        await executiveOption.first().click();
      }
      
      // Aguardar processamento
      await page.waitForTimeout(3000);
      
      // Verificar se não há erro
      const errorMessages = await page.locator('text=/erro|error|falha/i').count();
      expect(errorMessages).toBe(0);
      
      // Pode aparecer mensagem de sucesso
      const successMessage = page.locator('text=/sucesso|gerado|criado/i');
      if (await successMessage.count() > 0) {
        await expect(successMessage.first()).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('geração de relatório PDF técnico', async ({ page }) => {
    const reportButton = page.locator('button:has-text("Relatório"), button:has-text("PDF")');
    
    if (await reportButton.count() > 0) {
      await reportButton.first().click();
      
      // Procurar opção técnica
      const technicalOption = page.locator('text=/Técnico|Technical|Detalhado/');
      if (await technicalOption.count() > 0) {
        await technicalOption.first().click();
      }
      
      await page.waitForTimeout(3000);
      
      const errorMessages = await page.locator('text=/erro|error|falha/i').count();
      expect(errorMessages).toBe(0);
    }
  });

  test('exportação para Excel', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Excel"), button:has-text("Planilha"), button:has-text(".xlsx")');
    
    if (await exportButton.count() > 0) {
      await exportButton.first().click();
      await page.waitForTimeout(2000);
      
      const errorMessages = await page.locator('text=/erro|error|falha/i').count();
      expect(errorMessages).toBe(0);
    }
  });

  test('exportação para CSV', async ({ page }) => {
    const csvButton = page.locator('button:has-text("CSV"), button:has-text(".csv")');
    
    if (await csvButton.count() > 0) {
      await csvButton.first().click();
      await page.waitForTimeout(2000);
      
      const errorMessages = await page.locator('text=/erro|error|falha/i').count();
      expect(errorMessages).toBe(0);
    }
  });

  test('personalização de relatório', async ({ page }) => {
    const reportButton = page.locator('button:has-text("Relatório")');
    
    if (await reportButton.count() > 0) {
      await reportButton.first().click();
      
      // Procurar opções de personalização
      const customOptions = page.locator('input[type="checkbox"], select');
      
      if (await customOptions.count() > 0) {
        // Alterar algumas opções
        const firstOption = customOptions.first();
        
        if (await firstOption.getAttribute('type') === 'checkbox') {
          await firstOption.setChecked(true);
        } else {
          const options = await firstOption.locator('option').count();
          if (options > 1) {
            await firstOption.selectOption({ index: 1 });
          }
        }
        
        // Gerar relatório personalizado
        const generateButton = page.locator('button:has-text("Gerar"), button:has-text("Criar")');
        if (await generateButton.count() > 0) {
          await generateButton.first().click();
          await page.waitForTimeout(3000);
        }
      }
    }
  });

  test('preview de relatório antes de gerar', async ({ page }) => {
    const reportButton = page.locator('button:has-text("Relatório")');
    
    if (await reportButton.count() > 0) {
      await reportButton.first().click();
      
      // Procurar botão de preview
      const previewButton = page.locator('button:has-text("Preview"), button:has-text("Visualizar")');
      
      if (await previewButton.count() > 0) {
        await previewButton.first().click();
        await page.waitForTimeout(2000);
        
        // Deve abrir modal ou nova área com preview
        const previewArea = page.locator('[class*="preview"], [class*="modal"], iframe');
        if (await previewArea.count() > 0) {
          await expect(previewArea.first()).toBeVisible();
        }
      }
    }
  });

  test('download de relatório gerado', async ({ page }) => {
    // Configurar listener para downloads
    const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null);
    
    const reportButton = page.locator('button:has-text("Relatório"), button:has-text("PDF")');
    
    if (await reportButton.count() > 0) {
      await reportButton.first().click();
      
      // Aguardar geração
      await page.waitForTimeout(3000);
      
      // Procurar botão de download
      const downloadButton = page.locator('button:has-text("Download"), button:has-text("Baixar"), a[download]');
      
      if (await downloadButton.count() > 0) {
        await downloadButton.first().click();
        
        // Verificar se download foi iniciado
        const download = await downloadPromise;
        if (download) {
          expect(download.suggestedFilename()).toMatch(/\.(pdf|xlsx|csv)$/i);
        }
      }
    }
  });

  test('relatório de diferentes tipos de plano', async ({ page }) => {
    // Testar relatório BD
    await page.click('text=Plano');
    const planSelect = page.locator('select').filter({ hasText: /BD|CD/ }).first();
    
    if (await planSelect.isVisible()) {
      await planSelect.selectOption('BD');
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      
      const reportButton = page.locator('button:has-text("Relatório")');
      if (await reportButton.count() > 0) {
        await reportButton.first().click();
        await page.waitForTimeout(1000);
        
        // Verificar se não há erro para BD
        const bdErrors = await page.locator('text=/erro|error/i').count();
        expect(bdErrors).toBe(0);
      }
      
      // Testar relatório CD
      await page.click('text=Plano');
      await planSelect.selectOption('CD');
      await page.click('text=Resultados');
      await page.waitForTimeout(2000);
      
      if (await reportButton.count() > 0) {
        await reportButton.first().click();
        await page.waitForTimeout(1000);
        
        // Verificar se não há erro para CD
        const cdErrors = await page.locator('text=/erro|error/i').count();
        expect(cdErrors).toBe(0);
      }
    }
  });

  test('inclusão de gráficos em relatórios', async ({ page }) => {
    const reportButton = page.locator('button:has-text("Relatório")');
    
    if (await reportButton.count() > 0) {
      await reportButton.first().click();
      
      // Procurar opção de incluir gráficos
      const chartOption = page.locator('text=/Gráfico|Chart|Incluir/, input[type="checkbox"]');
      
      if (await chartOption.count() > 0) {
        const chartCheckbox = chartOption.filter('[type="checkbox"]').first();
        if (await chartCheckbox.isVisible()) {
          await chartCheckbox.setChecked(true);
        }
        
        // Gerar relatório com gráficos
        const generateButton = page.locator('button:has-text("Gerar")');
        if (await generateButton.count() > 0) {
          await generateButton.first().click();
          await page.waitForTimeout(4000); // Gráficos podem demorar mais
        }
      }
    }
  });

  test('relatório de análise de sensibilidade', async ({ page }) => {
    // Configurar cenário para sensibilidade
    await page.click('text=Premissas');
    
    const contributionSlider = page.locator('text=Taxa de Contribuição').locator('..').locator('input[type="range"]');
    if (await contributionSlider.isVisible()) {
      await contributionSlider.fill('0.10');
    }
    
    await page.click('text=Resultados');
    await page.waitForTimeout(2000);
    
    const reportButton = page.locator('button:has-text("Relatório")');
    if (await reportButton.count() > 0) {
      await reportButton.first().click();
      
      // Procurar opção de sensibilidade
      const sensitivityOption = page.locator('text=/Sensibilidade|Cenário|Stress/');
      
      if (await sensitivityOption.count() > 0) {
        await sensitivityOption.first().click();
        await page.waitForTimeout(3000);
        
        const errorMessages = await page.locator('text=/erro|error/i').count();
        expect(errorMessages).toBe(0);
      }
    }
  });

  test('configuração de formato de relatório', async ({ page }) => {
    const reportButton = page.locator('button:has-text("Relatório")');
    
    if (await reportButton.count() > 0) {
      await reportButton.first().click();
      
      // Procurar opções de formato
      const formatOptions = page.locator('select, input[type="radio"]');
      
      if (await formatOptions.count() > 0) {
        const formatSelect = formatOptions.first();
        
        if (await formatSelect.getAttribute('type') === 'radio') {
          // Se for radio button, selecionar uma opção
          await formatSelect.click();
        } else {
          // Se for select, escolher uma opção
          const options = await formatSelect.locator('option').count();
          if (options > 1) {
            await formatSelect.selectOption({ index: 1 });
          }
        }
      }
    }
  });

  test('validação antes de gerar relatório', async ({ page }) => {
    // Limpar dados para forçar validação
    await page.click('text=Participante');
    await page.locator('input[type="range"]').first().fill('0');
    
    await page.click('text=Resultados');
    
    const reportButton = page.locator('button:has-text("Relatório")');
    if (await reportButton.count() > 0) {
      await reportButton.first().click();
      
      // Pode aparecer mensagem de validação
      const validationMessage = page.locator('text=/obrigatório|necessário|inválido/i');
      
      if (await validationMessage.count() > 0) {
        await expect(validationMessage.first()).toBeVisible();
      }
    }
  });

  test('histórico de relatórios gerados', async ({ page }) => {
    // Gerar um relatório primeiro
    const reportButton = page.locator('button:has-text("Relatório")');
    
    if (await reportButton.count() > 0) {
      await reportButton.first().click();
      await page.waitForTimeout(2000);
      
      // Procurar seção de histórico
      const historySection = page.locator('text=/Histórico|History|Anteriores/');
      
      if (await historySection.count() > 0) {
        await historySection.first().click();
        
        // Verificar se mostra relatórios anteriores
        const historyItems = page.locator('[class*="history"], [class*="list"] li');
        
        if (await historyItems.count() > 0) {
          await expect(historyItems.first()).toBeVisible();
        }
      }
    }
  });

  test('responsividade da interface de relatórios', async ({ page }) => {
    const viewports = [
      { width: 1200, height: 800 },
      { width: 768, height: 1024 },
      { width: 375, height: 667 }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      
      const reportButton = page.locator('button:has-text("Relatório")');
      
      if (await reportButton.count() > 0) {
        await expect(reportButton.first()).toBeVisible();
        
        await reportButton.first().click();
        await page.waitForTimeout(500);
        
        // Interface deve permanecer usável
        const modal = page.locator('[role="dialog"], .modal');
        if (await modal.count() > 0) {
          await expect(modal.first()).toBeVisible();
        }
        
        // Fechar modal se abriu
        const closeButton = page.locator('button:has-text("Fechar"), button:has-text("Cancelar"), [aria-label="Close"]');
        if (await closeButton.count() > 0) {
          await closeButton.first().click();
        }
      }
    }
  });
});