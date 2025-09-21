# Guia do Banco de Dados - PrevLab

## Visão Geral

O projeto agora utiliza **SQLite** com **SQLModel** para persistência de dados, oferecendo uma solução leve e eficiente para armazenar:

- 👥 **Perfis de usuário** e cenários salvos
- 📊 **Premissas atuariais** personalizáveis  
- 📈 **Tábuas de mortalidade** do sistema e customizadas
- 🔄 **Cache de resultados** de simulações

## Tecnologias Utilizadas

- **SQLModel**: ORM moderno compatível com Pydantic
- **SQLite**: Banco de dados em arquivo único
- **Alembic**: Migrações de banco de dados
- **FastAPI**: Integração nativa com dependency injection

## Estrutura do Banco

### Tabelas Principais

| Tabela | Descrição | Dados Armazenados |
|--------|-----------|-------------------|
| `user` | Usuários do sistema | ID, nome, email, timestamps |
| `userprofile` | Perfis/cenários salvos | Configurações completas do simulador em JSON |
| `mortalitytable` | Tábuas de mortalidade | Dados atuariais, metadados |
| `actuarialassumption` | Premissas atuariais | Parâmetros por categoria (taxas, crescimento, etc.) |
| `simulationresult` | Cache de resultados | Hash do estado + resultados serializados |

## Localização dos Arquivos

```
backend/
├── data/
│   └── simulador.db           # Arquivo do banco SQLite
├── src/
│   ├── database.py            # Configuração do banco
│   ├── models/
│   │   └── database.py        # Modelos SQLModel
│   ├── repositories/          # Camada de acesso aos dados
│   │   ├── base.py           # Repositório base
│   │   ├── user_repository.py
│   │   ├── mortality_repository.py
│   │   └── assumption_repository.py
│   └── scripts/
│       └── migrate_mortality_tables.py  # Script de migração inicial
```

## Inicialização e Migração

### Primeira Execução

O banco é criado automaticamente quando a aplicação inicia. Execute:

```bash
# O script já foi executado, mas pode ser rodado novamente se necessário
uv run python src/scripts/migrate_mortality_tables.py
```

### Dados Iniciais Criados

- **4 Tábuas de mortalidade**: BR_EMS_2021, AT_2000, IBGE_2018_M, IBGE_2018_F
- **6 Premissas atuariais**: 3 taxas de desconto + 3 taxas de crescimento salarial

## Novos Endpoints da API

### Usuários e Perfis

- `POST /users` - Criar usuário
- `GET /users/{user_id}/profiles` - Listar perfis do usuário
- `POST /users/{user_id}/profiles` - Criar novo perfil
- `GET /users/{user_id}/profiles/{profile_id}` - Obter perfil específico
- `PUT /users/{user_id}/profiles/{profile_id}` - Atualizar perfil
- `DELETE /users/{user_id}/profiles/{profile_id}` - Deletar perfil
- `POST /users/{user_id}/profiles/{profile_id}/toggle-favorite` - Marcar como favorito

### Tábuas e Premissas

- `GET /mortality-tables` - Listar tábuas (agora do banco de dados)
- `GET /actuarial-assumptions` - Listar premissas atuariais
- `GET /actuarial-assumptions/categories` - Listar categorias de premissas

## Exemplos de Uso

### Criar Usuário

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "André Camatta", "email": "andre@exemplo.com"}'
```

### Salvar Cenário

```bash
curl -X POST "http://localhost:8000/users/1/profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_name": "Cenário Conservador",
    "description": "Premissas conservadoras para aposentadoria",
    "simulator_state": {
      "age": 30,
      "gender": "M",
      "salary": 8000.0,
      "discount_rate": 0.04,
      // ... demais parâmetros do SimulatorState
    }
  }'
```

### Recuperar Cenário Salvo

```bash
curl -X GET "http://localhost:8000/users/1/profiles/1"
```

## Vantagens da Implementação

✅ **Simplicidade**: SQLite em arquivo único, sem configuração de servidor  
✅ **Performance**: Queries locais, sem latência de rede  
✅ **Compatibilidade**: SQLModel mantém compatibilidade total com Pydantic  
✅ **Flexibilidade**: JSON para dados complexos (estados do simulador)  
✅ **Backup Fácil**: Copiar arquivo `simulador.db` para backup completo  
✅ **Desenvolvimento**: Não requer instalação de banco externo  

## Manutenção

### Backup

```bash
cp data/simulador.db data/backup_$(date +%Y%m%d_%H%M%S).db
```

### Reset do Banco (Desenvolvimento)

```python
from src.database import reset_database
reset_database()  # CUIDADO: Remove todos os dados
```

### Verificar Dados

```bash
sqlite3 data/simulador.db
.tables
.schema mortalitytable
SELECT * FROM user;
```

## Próximos Passos Opcionais

- 🔄 **Alembic migrations** para versionamento do schema
- 📊 **Dashboards de uso** com estatísticas dos perfis salvos
- 🔐 **Autenticação** com JWT para multi-tenancy
- 📦 **PostgreSQL** para deployment em produção (mantendo compatibilidade)
- 🔍 **Full-text search** nos perfis salvos
- 📈 **Analytics** de simulações mais executadas

---

A implementação está completa e funcional. O simulador agora persiste dados de forma eficiente mantendo toda a simplicidade original do projeto! 🚀