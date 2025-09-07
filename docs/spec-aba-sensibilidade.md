# Especificação — Aba “Sensibilidade” com Tornados

## Objetivo
- Criar uma nova aba “Sensibilidade” no frontend que permita analisar de forma visual e comparável o impacto das principais premissas sobre métricas‑chave do sistema (ex.: RMBA para BD; Renda Mensal/Taxa de Reposição para CD), usando gráficos do tipo “tornado” e painéis complementares.

## Escopo
- Frontend: nova aba, gráficos (tornado), seletor de métrica/variável, tooltips e estados de carregamento/erro/vazio.
- Backend: uso dos dados de sensibilidade já existentes para BD; opcionalmente estender para CD (ver “Backend – extensões CD”).
- Sem dependências novas além do Chart.js já utilizado.

## Métrica‑alvo por tipo de plano
- Plano BD:
  - Métrica padrão do tornado: RMBA (R$).
  - Alternativas opcionais (futuro): Déficit/Superávit (R$), Required Contribution Rate (%).
- Plano CD:
  - Métrica padrão do tornado: Renda Mensal na Aposentadoria (R$) ou Taxa de Reposição (%).
  - Escolha da métrica por toggle (radio) no topo da aba (default: Renda Mensal).

## Fontes de dados
- Já disponível no backend (para BD):
  - `results.sensitivity_discount_rate: Record<number, number>` → RMBA para diferentes taxas de desconto
  - `results.sensitivity_mortality: Record<string, number>` → RMBA por tábua
  - `results.sensitivity_retirement_age: Record<number, number>` → RMBA por idade de aposentadoria
  - `results.sensitivity_salary_growth: Record<number, number>` → RMBA por crescimento salarial
  - `results.sensitivity_inflation: Record<number, number>` → atualmente vazio (manter oculto)
- Baseline para deltas: `results.rmba` (BD) e, no caso de CD, `results.monthly_income_cd` ou `results.replacement_ratio` conforme métrica selecionada.

## Backend — extensões CD (opcional, recomendado)
- Objetivo: expor dados análogos de sensibilidade para CD com base na métrica selecionada.
- Proposta mínima:
  - Adicionar ao `SimulatorResults` (backend e tipos no frontend):
    - `sensitivity_cd_accumulation_rate: Dict[float, float]` (variação da renda mensal);
    - `sensitivity_cd_conversion_rate: Dict[float, float]`;
    - Reusar `sensitivity_retirement_age` e `sensitivity_salary_growth` para CD calculando renda mensal/Taxa de Reposição sob variações.
  - Em `ActuarialEngine._calculate_cd_sensitivity` (hoje retorna dicts mas não são propagados), popular esses novos campos no retorno final.
- Alternativa sem backend (fase 2): no front, sob demanda, disparar pequenas variações do estado via `/calculate` e construir o tornado client‑side (com debounce e limite de 5–7 chamadas por interação). Preferir solução backend.

## UX / Layout
- Nova aba na navegação principal intitulada “Sensibilidade” com ícone `tune` ou `insights`.
- Estrutura:
  1) Header com título + seletor de métrica (em CD: “Renda Mensal | Taxa de Reposição”).
  2) Grid 2 colunas (desktop) / 1 coluna (mobile):
     - Coluna A: Tornado principal (Top 5 variáveis por impacto absoluto na métrica‑alvo).
     - Coluna B: Painéis auxiliares:
       - “Variável detalhada” (dropdown) → tornado de um único fator com intervalos (ex.: 4–8% p/ taxa de desconto).
       - “Cenários” (Base/Otimista/Pessimista): resumo side‑by‑side de métrica‑alvo, contribuição requerida e déficit/superávit (quando aplicável).
- Tooltips explicativos em cada variável (ex.: “Aumentar taxa de desconto tende a reduzir RMBA”).
- Tema e estilo: seguir `chartSetup.ts` e padrões de cor já usados (verde positivo, vermelho negativo; acinzentado neutro).

## Cálculo do Tornado (lógica)
- Base: para cada variável, use os pontos fornecidos por `results.sensitivity_*` (BD) ou pelos novos campos CD.
- Passos (BD → métrica RMBA):
  1) Definir baseline `B = results.rmba`.
  2) Para cada variável, selecionar 2 extremos “low” e “high” a partir do objeto de sensibilidade (ex.: menor e maior chave do dicionário).
  3) Calcular `Δlow = value(low) − B`, `Δhigh = value(high) − B`.
  4) Usar barras horizontais com origem no zero; valores negativos à esquerda, positivos à direita.
  5) Ordenar variáveis por `max(|Δlow|, |Δhigh|)` (maior impacto no topo).
- Passos (CD → métrica Renda Mensal):
  1) Definir baseline `B = results.monthly_income_cd` (ou `results.replacement_ratio`).
  2) Repetir procedimento acima usando os campos de sensibilidade para CD.
- Formatação:
  - Unidades: R$ para renda/RMBA/Δ; % para Taxa de Reposição.
  - Datalabels: mostrar o valor absoluto do impacto (ex.: “+R$ 1.200”).
  - Cores: positivo (ganho de renda/queda de RMBA) em verde; negativo em vermelho. Inverter legenda se métrica for RMBA (queda pode ser desejável). Incluir legenda “Sinal interpretado em relação à atratividade”.

## Estados e Comportamento
- Loading: skeleton do gráfico + placeholders.
- Sem dados:
  - BD: se dicionários estiverem vazios, mostrar aviso “Execute a simulação”/“Sem sensibilidade disponível”.
  - CD: se não implementado no backend, exibir chamada “Em breve” e opção de gerar análise on‑demand (desativada por padrão nesta fase).
- Erro: mensagem amigável com tentativa de recarregar.

## Acessibilidade e Responsividade
- WCAG AA: contraste adequado nas barras; tooltips acessíveis.
- Teclado: navegação entre variáveis (dropdown e toggles) com `tab`/`enter`.
- Mobile: tornado em 1 coluna com rolagem horizontal opcional se necessário; títulos curtos.

## Testes
- Unit (frontend):
  - Ordenação correta por impacto absoluto.
  - Cálculo de deltas vs baseline.
  - Formatação (R$ e %), sinal e cores.
  - Renderização por tipo de plano (BD/CD) e métrica selecionada (CD).
- E2E (Playwright):
  - Aba “Sensibilidade” aparece e troca entre abas funciona.
  - Tooltips e seleção de variável/métrica funcionam.
  - Estados de loading/empty/erro exibidos corretamente.

## Desempenho
- Renderização única por atualização de `results`.
- Evitar recomputar deltas em cada render (memoização por `useMemo`).
- Sem chamadas adicionais ao backend na fase 1 (usar apenas `results`).

## Entregáveis
- Nova aba visível “Sensibilidade”.
- Tornado principal (Top 5 variáveis) + painel detalhado por variável.
- Suporte completo para BD; placeholder para CD (ou sensibilidade CD se backend estendido).

## Roteiro de implementação (passo a passo)
1) UI
- Adicionar a aba:
  - Editar `simulador-atuarial-individual/frontend/src/design-system/components/TabNavigation.tsx` para incluir `{ id: 'sensitivity', label: 'Sensibilidade', icon: 'tune' }`.
  - Ajustar `TabbedDashboard` para case `sensitivity`.
- Criar componentes:
  - `frontend/src/components/charts/TornadoChart.tsx`: wrapper com Chart.js (Horizontal Bar), recebendo lista de itens `{ label, deltaLow, deltaHigh, unit, tooltip }`.
  - `frontend/src/components/tabs/SensitivityTab.tsx`: 
    - Header + seletor de métrica (apenas CD);
    - Tornado principal (agrega variáveis);
    - Seletor de “variável detalhada” e tornado secundário daquela variável.
- Utilidades:
  - Reusar `getZeroLineGridConfig` e formatações de `formatBR`.

2) Integração de dados
- Converter objetos de `results.sensitivity_*` em lista de itens do tornado.
- Baseline: `results.rmba` (BD) ou `results.monthly_income_cd`/`results.replacement_ratio` (CD).
- Mapear nomes amigáveis:
  - Desconto → “Taxa de Desconto (a.a.)”; Mortalidade → “Tábua de Mortalidade”; Idade Aposent. → “Idade de Aposentadoria”; Cresc. Salarial → “Crescimento Salarial (a.a.)”.

3) Backend (opcional para CD)
- Popular no `SimulatorResults` campos:
  - `sensitivity_cd_accumulation_rate: Dict[float, float]`;
  - `sensitivity_cd_conversion_rate: Dict[float, float]`;
  - Reusar/estender `sensitivity_retirement_age` e `sensitivity_salary_growth` para CD;
- Atualizar `frontend/src/types/simulator.types.ts` com os novos campos.

## Critérios de Aceite
- A aba “Sensibilidade” aparece e ativa sem quebrar as demais abas.
- Em BD:
  - O tornado exibe pelo menos 4 variáveis (desconto, mortalidade, idade, crescimento) ordenadas por impacto.
  - Deltas são calculados corretamente vs `results.rmba` e exibidos com sinal e unidade certos.
- Em CD (fase 1):
  - Mostra placeholder e instruções para ativar sensibilidade CD ou toggle de métrica.
- Responsividade: gráfico legível em 320px e acima; tooltips funcionam.
- Testes unitários de cálculo e renderização passam; e2e básico de navegação e render.

## Pseudocódigo — preparo dos dados do tornado (BD)
```ts
// baseline
const B = results.rmba;

// helper: transforma dict {key: value} em [minKey, maxKey, minVal, maxVal]
function getExtremes(dict: Record<string | number, number>) {
  const entries = Object.entries(dict).map(([k, v]) => [Number(k) || k, v] as const);
  if (!entries.length) return null;
  const sorted = entries.sort((a, b) => (typeof a[0] === 'number' ? Number(a[0]) - Number(b[0]) : String(a[0]).localeCompare(String(b[0]))));
  const [lowK, lowV] = sorted[0];
  const [highK, highV] = sorted[sorted.length - 1];
  return { lowK, lowV, highK, highV };
}

const factors = [];
const d = results.sensitivity_discount_rate; // ex.: {0.04: rmbaX, 0.05: rmbaY, 0.06: rmbaZ}
const e = getExtremes(d);
if (e) factors.push({
  label: 'Taxa de Desconto (a.a.)',
  deltaLow: e.lowV - B,
  deltaHigh: e.highV - B,
  unit: 'R$'
});
// repetir para mortalidade, idade de aposentadoria, crescimento salarial

// ordenar por impacto absoluto
factors.sort((a, b) => Math.max(Math.abs(b.deltaLow), Math.abs(b.deltaHigh)) - Math.max(Math.abs(a.deltaLow), Math.abs(a.deltaHigh)));
```

## Arquivos a criar/alterar
- Criar:
  - `simulador-atuarial-individual/frontend/src/components/charts/TornadoChart.tsx`
  - `simulador-atuarial-individual/frontend/src/components/tabs/SensitivityTab.tsx`
- Alterar:
  - `simulador-atuarial-individual/frontend/src/design-system/components/TabNavigation.tsx` (adicionar aba)
  - `simulador-atuarial-individual/frontend/src/components/sections/TabbedDashboard.tsx` (render da nova aba)
  - (Opcional CD) Backend `actuarial_engine.py` para popular novos campos e `models/results.py`/`frontend/src/types/simulator.types.ts`.

## Observações
- “Inflation” está como placeholder no backend — manter oculto.
- Se mudanças em sinal causarem confusão (ex.: RMBA menor é bom), incluir legenda clara: “Barras à esquerda reduzem RMBA (melhoram o equilíbrio)”.
- Reaproveitar paleta e espaçamentos do design system.

---

Versão: 1.0 — Especificação inicial da aba de Sensibilidade.
