# Especificação de Melhorias de Design - Simulador Atuarial Individual

## 1. Visão Geral

Este documento detalha as sugestões de melhoria para a interface do usuário (UI) e a experiência do usuário (UX) do Simulador Atuarial Individual. O objetivo é modernizar o visual, melhorar a usabilidade e tornar a apresentação dos resultados mais clara e impactante.

## 2. Estrutura e Layout Principal

A mudança mais significativa é a **unificação das seções "Dados do Participante" e "Parâmetros" em uma única tela principal**. Isso cria um fluxo de trabalho mais coeso e elimina a necessidade de alternar entre abas para inserir dados.

### Layout Proposto:

- **Dois Painéis Principais:**
    1.  **Painel de Configuração (Esquerda):** Um painel fixo e rolável que conterá todos os campos de entrada (dados do participante e parâmetros do plano).
    2.  **Painel de Resultados (Direita):** Uma área dinâmica que exibe os resultados da simulação em tempo real, atualizando-se conforme os parâmetros são ajustados.

- **Barra Lateral (Sidebar):** A barra lateral atual será simplificada, mantendo a navegação principal, mas removendo as seções de entrada de dados que agora estarão no painel principal.
    - Ícones sugeridos: `Dashboard` (para a simulação), `Relatórios`, `Configurações`.

- **Cabeçalho (Header):** O cabeçalho será mais limpo, focando no título da página e em ações globais, como "Resetar Simulação" e talvez um botão "Salvar Cenário".

**Estrutura do Código (`App.tsx`):**

```tsx
<div className="flex h-screen bg-gray-50">
  <Sidebar />
  <div className="flex-1 flex flex-col overflow-hidden">
    <Header />
    <main className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 overflow-y-auto">
      {/* Coluna de Configuração */}
      <div className="space-y-6">
        <ParticipantCard state={state} onStateChange={updateState} />
        <FinancialAssumptionsCard state={state} onStateChange={updateState} />
        <ActuarialBasisCard state={state} onStateChange={updateState} />
      </div>

      {/* Coluna de Resultados */}
      <div>
        <ResultsDashboard results={results} loading={loading} />
      </div>
    </main>
  </div>
</div>
```

## 3. Redesign dos Componentes de Entrada

Os formulários e controles de entrada serão organizados em "cartões" (cards) temáticos para melhorar a clareza e organização.

### 3.1. Cartão: Dados do Participante (`ParticipantCard.tsx`)

- **Agrupamento Lógico:** Campos como `Idade`, `Sexo`, `Salário`, `Tempo de Serviço` e `Saldo Inicial` serão agrupados neste cartão.
- **Inputs Visuais:**
    - Utilizar inputs com ícones e formatação de moeda (R$) para os campos de Salário e Saldo Inicial.
    - Melhorar o espaçamento e a tipografia para facilitar a leitura.
- **Info Tooltips:** Adicionar ícones de informação (`?`) ao lado de cada campo para explicar o seu propósito quando o usuário passar o mouse sobre eles.

### 3.2. Cartão: Premissas Financeiras (`FinancialAssumptionsCard.tsx`)

- **Agrupamento:** `Taxa de Acumulação`, `Taxa de Desconto`, `Crescimento Salarial Real`.
- **Sliders Interativos:**
    - Os sliders devem ter um design mais moderno.
    - O valor atual do slider deve ser exibido de forma proeminente e atualizar-se em tempo real.
    - Adicionar marcas de mínimo e máximo nas extremidades do slider.

### 3.3. Cartão: Base Atuarial (`ActuarialBasisCard.tsx`)

- **Agrupamento:** `Tábua de Mortalidade` e `Método de Cálculo`.
- **Seletores (Selects) Estilizados:** Modernizar a aparência dos menus suspensos para que correspondam ao novo design. O item selecionado deve ser claramente visível.

## 4. Redesign do Painel de Resultados (`ResultsDashboard.tsx`)

O painel de resultados é o foco principal da experiência. As informações devem ser apresentadas de forma hierárquica e visual.

### 4.1. Destaques Principais (KPIs)

- **Cards de Destaque:** Exibir os resultados mais importantes (`RMBA`, `RMBC`, e `Déficit/Superávit`) em cards grandes e proeminentes no topo do painel.
- **Feedback Visual de Cores:**
    - Usar **verde** consistentemente para resultados positivos (ex: Superávit).
    - Usar **vermelho/laranja** para resultados negativos ou de atenção (ex: Déficit, Taxa Necessária elevada).
- **Tipografia Clara:** Aumentar o tamanho da fonte para os valores principais para que sejam lidos rapidamente.

### 4.2. Gráfico de Projeção (Novo Componente)

- **Componente Sugerido:** `ProjectionChart.tsx`
- **Visualização:** Implementar um gráfico de barras ou linhas (usando uma biblioteca como `Recharts` ou `Chart.js`) que mostre a projeção do saldo de conta ao longo do tempo, contrastando com o passivo atuarial.
- **Interatividade:** Permitir que o usuário passe o mouse sobre o gráfico para ver os valores detalhados de cada ano.

### 4.3. Tabela de Métricas Detalhadas

- **Clareza e Espaçamento:** Substituir a lista atual por uma tabela bem formatada com linhas alternadas (`zebra stripes`) para facilitar a leitura.
- **Categorização:** Agrupar métricas relacionadas (ex: `Métricas-Chave`, `Decomposição Atuarial`) sob subtítulos claros dentro da tabela.

## 5. Paleta de Cores e Tipografia

- **Cores Primárias:**
    - **Azul (Ação/Principal):** `#3B82F6` (Azul-500 do Tailwind)
    - **Verde (Sucesso):** `#10B981` (Verde-500 do Tailwind)
    - **Vermelho (Alerta/Déficit):** `#EF4444` (Vermelho-500 do Tailwind)
- **Cores de Fundo:**
    - **Fundo da Página:** `#F9FAFB` (Cinza-50 do Tailwind)
    - **Fundo dos Cards:** `#FFFFFF` (Branco)
- **Tipografia:**
    - **Fonte Principal:** `Inter` ou outra fonte sans-serif moderna.
    - **Títulos:** `font-bold`
    - **Texto do Corpo:** `font-normal`, `text-gray-600`
    - **Valores de Destaque:** `font-bold`, `text-gray-900`

## 6. Plano de Implementação (Sugestão para o Desenvolvedor)

1.  **Refatorar `App.tsx`:** Implementar a nova estrutura de layout com grid de duas colunas.
2.  **Criar Cards de Configuração:**
    - `ParticipantCard.tsx`
    - `FinancialAssumptionsCard.tsx`
    - `ActuarialBasisCard.tsx`
3.  **Atualizar `ResultsDashboard.tsx`:** Aplicar o novo design com cards de KPI e a tabela de métricas redesenhada.
4.  **(Opcional) Adicionar `ProjectionChart.tsx`:** Implementar o gráfico de projeção.
5.  **Revisão Final:** Ajustar espaçamentos, cores e tipografia em toda a aplicação para garantir consistência.