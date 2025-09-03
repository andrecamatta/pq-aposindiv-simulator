const { chromium } = require('playwright');

(async () => {
  // Inicializar browser
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navegar para localhost:5173
    console.log('Navegando para localhost:5173...');
    await page.goto('http://localhost:5173');
    
    // Aguardar página carregar
    await page.waitForLoadState('networkidle');
    
    // Ir para aba "Participante"
    console.log('Clicando na aba Participante...');
    await page.click('text=Participante');
    
    // Aguardar um pouco para garantir que tudo carregou
    await page.waitForTimeout(1000);
    
    // Capturar screenshot da página completa
    await page.screenshot({ 
      path: 'screenshot-participante-full.png',
      fullPage: true 
    });
    console.log('Screenshot da página completa salvo: screenshot-participante-full.png');
    
    // Encontrar todos os sliders
    const sliders = await page.locator('[data-testid="slider"]').all();
    console.log(`Encontrados ${sliders.length} sliders`);
    
    // Capturar screenshot de cada slider individualmente
    for (let i = 0; i < sliders.length; i++) {
      const slider = sliders[i];
      const sliderBox = await slider.boundingBox();
      
      if (sliderBox) {
        // Expandir a área para incluir labels
        const expandedBox = {
          x: sliderBox.x - 50,
          y: sliderBox.y - 20,
          width: sliderBox.width + 100,
          height: sliderBox.height + 40
        };
        
        await page.screenshot({
          path: `screenshot-slider-${i + 1}.png`,
          clip: expandedBox
        });
        console.log(`Screenshot do slider ${i + 1} salvo: screenshot-slider-${i + 1}.png`);
      }
    }
    
    // Analisar elementos do slider para verificar alinhamento
    console.log('\n=== ANÁLISE DE ALINHAMENTO DOS SLIDERS ===');
    
    for (let i = 0; i < sliders.length; i++) {
      const slider = sliders[i];
      
      // Obter informações do trilho
      const track = slider.locator('.slider-track');
      const trackBox = await track.boundingBox();
      
      // Obter informações da bolinha
      const thumb = slider.locator('.slider-thumb');
      const thumbBox = await thumb.boundingBox();
      
      if (trackBox && thumbBox) {
        console.log(`\nSlider ${i + 1}:`);
        console.log(`  Trilho - Y: ${trackBox.y}, Height: ${trackBox.height}, Centro Y: ${trackBox.y + trackBox.height / 2}`);
        console.log(`  Bolinha - Y: ${thumbBox.y}, Height: ${thumbBox.height}, Centro Y: ${thumbBox.y + thumbBox.height / 2}`);
        
        const trackCenterY = trackBox.y + trackBox.height / 2;
        const thumbCenterY = thumbBox.y + thumbBox.height / 2;
        const difference = Math.abs(trackCenterY - thumbCenterY);
        
        console.log(`  Diferença entre centros: ${difference.toFixed(2)}px`);
        
        if (difference < 1) {
          console.log(`  ✅ ALINHAMENTO CORRETO (diferença < 1px)`);
        } else {
          console.log(`  ❌ ALINHAMENTO INCORRETO (diferença: ${difference.toFixed(2)}px)`);
        }
      }
    }
    
    // Verificar estilos CSS aplicados
    console.log('\n=== VERIFICAÇÃO DE ESTILOS CSS ===');
    
    const firstSlider = sliders[0];
    if (firstSlider) {
      const track = firstSlider.locator('.slider-track');
      const thumb = firstSlider.locator('.slider-thumb');
      
      const trackStyles = await track.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          height: styles.height,
          marginTop: styles.marginTop,
          position: styles.position
        };
      });
      
      const thumbStyles = await thumb.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          height: styles.height,
          width: styles.width,
          marginTop: styles.marginTop,
          position: styles.position
        };
      });
      
      console.log('Estilos do trilho:', trackStyles);
      console.log('Estilos da bolinha:', thumbStyles);
    }
    
  } catch (error) {
    console.error('Erro durante o teste:', error);
  } finally {
    await browser.close();
  }
})();