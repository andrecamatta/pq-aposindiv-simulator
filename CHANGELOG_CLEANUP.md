# Limpeza e Reorganização do Projeto - 2025-10-13

## 🧹 Resumo das Mudanças

Este documento registra a limpeza e reorganização realizada no projeto para melhorar a estrutura e remover arquivos obsoletos.

## 📁 Arquivos Removidos

### Raiz do Projeto
- ❌ `test_premissas_tab.py` - Script de debug temporário do Playwright (7KB)
- ❌ `screenshot_1_initial.png` - Screenshot de teste (15KB)
- ❌ `screenshot_error.png` - Screenshot de erro (8.5KB)
- ❌ `start` - Arquivo vazio sem propósito
- ❌ `logo.png` - Logo duplicado (1.9MB) - já existe em `frontend/public/`

### Backend
- ❌ `simulador-atuarial-individual/backend/simulador-atuarial-individual/` - Pasta duplicada aninhada (20KB)
- ❌ `simulador-atuarial-individual/backend/mortality_tables_config_generated.json` - Config gerado por script (4.5KB)

**Total liberado**: ~2MB

## 📦 Arquivos Movidos

### Testes
- ✅ `test_bd_cd_api_equivalence.py` → `backend/tests/`
- ✅ `test_cd_bd_equivalence.py` → `backend/tests/`

### Documentação
- ✅ `simulador-atuarial-individual/DEPLOY.md` → `docs/deployment/`
- ✅ `simulador-atuarial-individual/TESTE_DOCKER.md` → `docs/deployment/`
- ✅ `docs/especificacao-correcoes-atuariais.md` → `simulador-atuarial-individual/docs/`

### Dados de Referência
- ✅ `Hipóteses Atuariais por Plano - 2024.xlsx` → `docs/data-sources/`
- ✅ `simulador-atuarial-individual/backend/tabuas-br-ems-2010-2015-2021.xlsx` → `docs/data-sources/`

## 📂 Nova Estrutura de Documentação

```
docs/
├── README.md                              # Índice da documentação
├── deployment/                            # Deploy e infraestrutura
│   ├── DEPLOY.md                          # Guia de deploy em produção
│   └── TESTE_DOCKER.md                    # Troubleshooting Podman/Docker
└── data-sources/                          # Arquivos de referência
    ├── Hipóteses Atuariais por Plano - 2024.xlsx
    └── tabuas-br-ems-2010-2015-2021.xlsx
```

## 🔧 Atualizações em Arquivos

### `.gitignore`
Adicionado padrões para prevenir commit de arquivos temporários:
```gitignore
# Test artifacts and temporary files
screenshot_*.png
test_results.json
test_premissas_*.py
*_debug.py

# Generated configs (keep only the main ones)
*_generated.json
!package-lock.json
```

### `README.md`
- Atualizada estrutura do projeto
- Corrigido link para DEPLOY.md

### `docs/README.md` (novo)
- Criado índice da documentação
- Explicação da estrutura de docs

## ✅ Benefícios

1. **Melhor Organização**
   - Testes consolidados em `backend/tests/`
   - Documentação organizada por categoria
   - Dados de referência em local dedicado

2. **Mais Limpo**
   - Raiz do projeto sem arquivos temporários
   - Sem duplicação de arquivos
   - Sem pastas aninhadas desnecessárias

3. **Manutenção**
   - `.gitignore` atualizado previne futuros problemas
   - Estrutura clara facilita localização de arquivos
   - Documentação centralizada

4. **Espaço**
   - ~2MB de arquivos temporários removidos
   - Estrutura mais enxuta

## 🎯 Próximos Passos

Para manter o projeto organizado:

1. ✅ Sempre colocar testes em `backend/tests/` ou `frontend/tests/`
2. ✅ Usar `docs/deployment/` para documentação de infra
3. ✅ Colocar dados de referência em `docs/data-sources/`
4. ✅ Arquivos temporários de debug devem seguir padrão: `*_debug.py`, `screenshot_*.png`

## 📊 Impacto

- **Arquivos removidos**: 7
- **Arquivos movidos**: 7
- **Arquivos criados**: 2 (READMEs)
- **Arquivos atualizados**: 2 (.gitignore, README.md)
- **Espaço liberado**: ~2MB
- **Tempo de execução**: ~5 minutos

---

*Limpeza realizada em 2025-10-13 seguindo boas práticas de organização de projetos.*
