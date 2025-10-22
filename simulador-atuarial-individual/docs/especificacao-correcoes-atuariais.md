# Especificação de Correções Conceituais nos Cálculos Atuariais

Este documento detalha ajustes conceituais e técnicos a serem implementados no simulador atuarial, visando padronização metodológica, consistência entre módulos e alinhamento com práticas atuariais usuais.

## Objetivos

- Padronizar a conversão de mortalidade anual → mensal.
- Alinhar o uso de probabilidades de sobrevivência (tPx) ao timing do pagamento (antecipado/postecipado).
- Corrigir o cálculo do VPA do benefício alvo na análise de suficiência.
- Parametrizar o timing na anuidade atuarial utilizada na conversão CD.
- Revisar o uso de fatores anuais quando os fluxos já são modelados mensalmente com pagamentos extras (13º/14º).
- Deixar explícita a modelagem da taxa administrativa (antes e após a aposentadoria) e sua interação com VPAs.

## Contexto e Problemas Identificados

1. Mortalidade mensal inconsistente
   - Onde:  (função ).
   - Problema: usa aproximação . O restante do código usa .
   - Impacto: viés em tPx mensais e, portanto, nos VPAs.

2. tPx não ajustado ao timing do pagamento
   - Onde: 
     -  (funções , ).
     -  (funções de VPA para benefícios/contribuições/alvo).
     -  (fatores de anuidade).
   - Problema: o timing só afeta o desconto; a sobrevivência usada é sempre “fim de período”.
   - Impacto: subavalia a 1ª parcela em anuidades “antecipadas” e distorce a comparação entre timing.

3. Primeira parcela pós-aposentadoria na suficiência
   - Onde:  (método ).
   - Problema: para postecipado, a primeira parcela após a aposentadoria deveria usar tPx do final do primeiro mês de concessão; o código atual usa diretamente  na 1ª parcela.
   - Impacto: ligeira sub/superavaliação do VPA do benefício alvo.

4. Anuidade atuarial na conversão CD sem timing explícito
   - Onde:  (método ).
   - Problema: soma PV a partir de  com tPx já de 1 mês, misturando premissas de timing.
   - Impacto: fator de anuidade e renda mensal podem ficar enviesados para certos timings.

5. Custo Normal (PUC/EAN) simplificado
   - Onde:  (método ).
   - Observação: implementação atual é uma aproximação; melhoria futura recomendada (fora do escopo crítico imediato).

6. Ajuste semestral em fatores anuais (0,5 mês)
   - Onde:  (classe ).
   - Problema: aplica  em fatores anuais quando os fluxos já são modelados mês a mês com 13º/14º.
   - Impacto: risco de dupla contagem/ajuste implícito; recomenda-se remover para simplificar.

7. Taxa administrativa e VPA de contribuições
   - Onde:  ().
   - Observação: modelagem via “fator de erosão” pré-aposentadoria é aceitável, mas explicitar decisão: aplica-se ou não taxa também no pós (benefícios)?

## Requisitos Funcionais

- RF1: Converter mortalidade anual → mensal por  em todos os locais.
- RF2: Ajustar tPx ao timing do pagamento:
  - Antecipado (due): parcela no início do mês usa tPx do início (t=0 → 1.0; t>0 → tPx do mês anterior).
  - Postecipado (immediate): parcela no fim do mês usa tPx do fim do mês (como hoje).
- RF3: No VPA do benefício alvo na suficiência, a 1ª parcela pós-aposentadoria deve respeitar o timing selecionado.
- RF4: Parametrizar timing na anuidade atuarial de CD.
- RF5: Remover o ajuste  dos fatores anuais quando os fluxos já consideram pagamentos extras mensalmente.
- RF6: Manter modelagem de taxa administrativa como “erosão” das contribuições pré-aposentadoria; documentar decisão para fase pós.

## Especificação Matemática

- Conversão de mortalidade:
  - Dado  (anual), ; .
- VPA padrão:
  - , onde  (antecipado) ou  (postecipado).
- tPx conforme timing:
  - Antecipado: usar  (com ) para a parcela em .
  - Postecipado: usar .

## Escopo Detalhado por Arquivo

1. 
   - Função :
     - Trocar a linha da conversão mensal para  e .
   - Funções  e :
     - Incluir lógica de tPx conforme timing:
       - Antecipado: dividir o loop em  com tPx=1.0 e para  usar tPx do mês anterior.
       - Postecipado: manter tPx do período.

2. 
   -  e :
     - Aplicar tPx ajustado ao timing (antecipado/postecipado) além do ajuste no desconto.
     - Pseudocódigo por parcela no mês :
       -  (com ).
       - ; acumular  se ambos > 0.

3. 
   - , , :
     - Alinhar tPx ao timing conforme regra acima.
     - Alternativamente, substituir por chamadas de  para reduzir duplicidade.

4. 
   -  (VPA do benefício alvo):
     - Corrigir 1ª parcela pós-aposentadoria:
       - Postecipado: usar  do primeiro mês concedido (fim do mês de concessão).
       - Antecipado: primeira parcela com  deve usar tPx=1.0.
     - Recomendação: gerar um fluxo unitário via  ao invés de laço manual para consistência.
   -  (CD):
     - Parametrizar timing do pagamento (usar ):
       - Postecipado: iniciar em  com  e desconto .
       - Antecipado: incluir termo  com  e desconto .
     - Opcional: considerar pagamentos extras (13º/14º) como feito em .
   - :
     - Remover  dos fatores anuais quando os fluxos já contemplarem pagamentos extras mensalmente.

5. Taxa administrativa
   - Manter  aplicando “fator de erosão” sobre contribuições pré-aposentadoria.
   - Decisão de produto: aplicar ou não taxa administrativa também na fase de pagamento (benefícios). Se “sim”, documentar e aplicar lógica análoga sobre o saldo durante fase pós.

## Testes a Implementar/Atualizar

- T1: Conversão de taxas
  - Garantir que  e  são inversas dentro de tolerância.
- T2: Mortalidade mensal
  - Verificar que  calculado por  substitui  e reduz discrepâncias.
- T3: Timing vs tPx
  - Caso sintético com  decrescente e :
    -  deve produzir VPA maior que  (mesmas taxas), ceteris paribus.
- T4: Suficiência – 1ª parcela
  - Verificar que a 1ª parcela pós-aposentadoria respeita o timing configurado.
- T5: CD – anuidade atuarial
  - Validar que o fator de anuidade muda conforme o timing e que a renda é consistente com um cálculo de referência.
- T6: Regressões
  - Garantir que resultados se mantêm determinísticos e dentro de ranges razoáveis dos testes existentes.

## Aceite / Critérios de Conclusão

- A. Todas as chamadas de VPA usam tPx compatível com o timing.
- B. Conversão de mortalidade padronizada por  em todo o código.
- C. Suficiência calcula VPA do benefício alvo com 1ª parcela correta.
- D. Conversão CD (atuarial) respeita o timing parametrizado.
- E. Removido o ajuste  quando redundante; comportamento anual permanece coerente com os fluxos mensais.
- F. Testes T1–T6 passando.

## Riscos e Decisões de Produto

- Aplicação da taxa administrativa no pós-aposentadoria pode reduzir benefícios e alterar métricas; requer validação com stakeholders.
- Inclusão de pagamentos extras (13º/14º) na anuidade atuarial de CD aumenta realismo, mas também complexidade computacional.

## Plano de Entrega

1. Refatorar utilitários (, ) e padronizar mortalidade/timing.
2. Ajustar pontos do engine (, , ).
3. Remover/ajustar o fator anual com meia-periodicidade quando redundante.
4. Atualizar/Adicionar testes (unitários e fumaça) conforme seção de testes.
5. Revisão técnica e validação com casos-sintéticos e um caso real.
6. Merge e tagging da versão.

## Referências de Código

- 
- 
- 
- 
- 

---

Dúvidas e decisões pendentes devem ser registradas neste arquivo para histórico.

