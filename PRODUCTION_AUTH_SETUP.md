# 🚀 Setup de Autenticação em Produção - Railway

**URL de Produção:** https://pq-aposindiv-simulator-production.up.railway.app/

---

## 📋 Checklist de Setup

- [ ] **Passo 1**: Configurar Google OAuth Console
- [ ] **Passo 2**: Configurar variáveis de ambiente no Railway
- [ ] **Passo 3**: Fazer redeploy (se necessário)
- [ ] **Passo 4**: Testar autenticação em produção

---

## 1️⃣ Configurar Google OAuth Console

### Acessar: https://console.cloud.google.com/

1. **Selecionar ou criar projeto**
   - Se já tem um projeto, selecione
   - Se não, crie um novo: "PrevLab" ou "Simulador Atuarial"

2. **Navegar para APIs & Services → Credentials**
   - Menu lateral: APIs & Services → Credentials

3. **Criar OAuth 2.0 Client ID** (se ainda não criou)
   - Clique em "Create Credentials" → "OAuth client ID"
   - **Application type**: Web application
   - **Name**: PrevLab Production (ou qualquer nome descritivo)

4. **Configurar Authorized redirect URIs**

   Adicione estas URLs:
   ```
   https://pq-aposindiv-simulator-production.up.railway.app/auth/success
   ```

   **Opcional** - Para testar local também:
   ```
   http://localhost:5173/auth/success
   ```

5. **Copiar credenciais**
   - **Client ID**: algo como `123456789-abc123.apps.googleusercontent.com`
   - **Client secret**: algo como `GOCSPX-abc123xyz456`

   ⚠️ **GUARDE ESSAS CREDENCIAIS** - você vai precisar no próximo passo!

---

## 2️⃣ Configurar Variáveis de Ambiente no Railway

### Acessar: https://railway.app/

1. **Navegar para o projeto**
   - Abra o projeto do simulador
   - Clique no serviço (backend)

2. **Ir para Variables**
   - Aba "Variables" no menu superior

3. **Adicionar/Editar as seguintes variáveis:**

```bash
# ========== AUTENTICAÇÃO (OBRIGATÓRIO) ==========
ENABLE_AUTH=true

# Google OAuth Credentials (copiar do Google Console)
GOOGLE_CLIENT_ID=SEU-CLIENT-ID-AQUI.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-SEU-CLIENT-SECRET-AQUI
GOOGLE_REDIRECT_URI=https://pq-aposindiv-simulator-production.up.railway.app/auth/success

# SECRET_KEY para JWT (gerar novo ou usar o existente)
# Para gerar novo: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<copie-do-.env-ou-gere-novo>
```

4. **Salvar**
   - Railway fará redeploy automaticamente quando você salvar

---

## 3️⃣ Verificar Redeploy

O Railway deve fazer redeploy automático após adicionar variáveis.

**Verificar:**
- Dashboard do Railway → Ver logs do build
- Aguardar deploy completar (~2-5 minutos)

---

## 4️⃣ Testar em Produção

### 4.1. Testar Health Check

```bash
curl https://pq-aposindiv-simulator-production.up.railway.app/auth/health
```

**Resposta esperada:**
```json
{
  "status": "ok",
  "config": {
    "configured": true,
    "enabled": true,
    "secret_key_configured": true,
    "google_client_id_configured": true,
    "google_client_secret_configured": true,
    "google_redirect_uri_configured": true
  }
}
```

⚠️ Se `configured: false`, revise as variáveis de ambiente!

### 4.2. Testar Login Completo

1. Acesse: https://pq-aposindiv-simulator-production.up.railway.app/
2. Deve redirecionar para `/login`
3. Clique em "Continuar com Google"
4. Faça login com sua conta Google
5. Deve ser redirecionado de volta para o simulador
6. Deve aparecer seu nome e avatar no header

---

## 🔍 Troubleshooting

### Problema: "redirect_uri_mismatch"

**Causa:** URL de redirect não está configurada no Google Console

**Solução:**
1. Volte ao Google Console
2. Verifique que a URL está exatamente como:
   ```
   https://pq-aposindiv-simulator-production.up.railway.app/auth/success
   ```
3. Sem trailing slash `/` no final!
4. Aguarde 5 minutos após salvar (Google pode demorar)

### Problema: "Autenticação não está configurada corretamente"

**Causa:** Variáveis de ambiente faltando ou incorretas

**Solução:**
1. Teste o endpoint: `/auth/health`
2. Veja qual campo está `false` no `config`
3. Adicione/corrija a variável correspondente no Railway

### Problema: Loop de redirecionamento

**Causa:** GOOGLE_REDIRECT_URI incorreto

**Solução:**
1. Verificar que `GOOGLE_REDIRECT_URI` no Railway é exatamente:
   ```
   https://pq-aposindiv-simulator-production.up.railway.app/auth/success
   ```
2. Sem trailing slash!
3. Deve ser idêntico ao configurado no Google Console

### Problema: Token inválido/expirado

**Causa:** SECRET_KEY mudou entre deploys

**Solução:**
1. Gere um novo SECRET_KEY:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Configure no Railway
3. Certifique-se que é o MESMO em todos os deploys
4. Limpe o localStorage do navegador (F12 → Application → Clear)

---

## 🎯 Resumo Rápido

Para ativar auth em produção:

1. **Google Console** → Criar OAuth Client → Copiar ID e Secret
2. **Railway Variables** → Adicionar:
   - `ENABLE_AUTH=true`
   - `GOOGLE_CLIENT_ID=...`
   - `GOOGLE_CLIENT_SECRET=...`
   - `GOOGLE_REDIRECT_URI=https://pq-aposindiv-simulator-production.up.railway.app/auth/success`
   - `SECRET_KEY=...`
3. **Aguardar redeploy** → Testar `/auth/health`
4. **Testar login** → https://pq-aposindiv-simulator-production.up.railway.app/

---

## ✅ Checklist Final

Antes de considerar concluído:

- [ ] `/auth/health` retorna `"enabled": true` e `"configured": true`
- [ ] Consegue acessar a URL principal e é redirecionado para `/login`
- [ ] Consegue clicar em "Continuar com Google"
- [ ] Consegue fazer login e ver o dashboard
- [ ] Nome e avatar aparecem no header
- [ ] Consegue fazer logout

---

**Data de configuração:** _____________

**Google Client ID usado:** _____________

**SECRET_KEY usado:** `<guardado no Railway Variables>`
