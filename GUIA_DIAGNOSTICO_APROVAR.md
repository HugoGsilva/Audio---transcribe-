# 🔍 GUIA DE DIAGNÓSTICO - Botão Aprovar Usuário

**Data:** 12/12/2025 12:19  
**Problema:** Botão de aprovar usuário não funciona

---

## ✅ CORREÇÕES APLICADAS

### 1. Logs de Debug Adicionados

**Frontend (`script.js`):**
- ✅ Console.log quando função é chamada
- ✅ Console.log do ID do usuário
- ✅ Console.log da resposta do servidor
- ✅ Mensagens de erro detalhadas

**Backend (`main.py`):**
- ✅ Log quando endpoint é chamado
- ✅ Log do usuário que está aprovando
- ✅ Log de sucesso com detalhes
- ✅ Log de erro se usuário não for encontrado

---

## 🧪 COMO TESTAR

### Passo 1: Abrir Console do Navegador
1. Abra http://localhost:8000/login
2. Pressione **F12** para abrir DevTools
3. Vá para a aba **Console**
4. Deixe aberto durante o teste

### Passo 2: Fazer Login como Admin
1. Usuário: `admin`
2. Senha: (vazio ou qualquer coisa)
3. Clique em "Entrar"

### Passo 3: Ir para Painel Admin
1. Clique em **"Admin"** no menu lateral
2. Aguarde carregar a lista de usuários

### Passo 4: Tentar Aprovar Usuário
1. Localize o usuário pendente na seção "Usuários Pendentes"
2. Clique no botão **"Aprovar"** (verde)
3. **OBSERVE O CONSOLE** - deve aparecer:
   ```
   approveUser called with id: [uuid-do-usuario]
   Sending POST to /api/admin/approve/[uuid]
   Response status: 200
   Success response: {message: "Usuário aprovado", ...}
   ```

### Passo 5: Verificar Resultado

**Se funcionar:**
- ✅ Toast verde: "Usuário aprovado com sucesso!"
- ✅ Usuário some da lista de pendentes
- ✅ Usuário aparece em "Todos os Usuários" com status "Ativo"

**Se NÃO funcionar:**
- ❌ Mensagem de erro no console
- ❌ Alert com mensagem de erro

---

## 📋 POSSÍVEIS ERROS E SOLUÇÕES

### Erro 1: "Acesso exclusivo para administradores"
**Causa:** Usuário não é admin  
**Solução:** Verificar se fez login com usuário "admin"

### Erro 2: "Usuário não encontrado"
**Causa:** ID do usuário está incorreto  
**Solução:** Verificar no console qual ID está sendo enviado

### Erro 3: "Could not validate credentials"
**Causa:** Token expirado  
**Solução:** Fazer logout e login novamente

### Erro 4: Nenhum erro, mas não atualiza
**Causa:** Problema na função loadAdminUsers  
**Solução:** Verificar logs do console

---

## 🔍 VERIFICAR LOGS DO SERVIDOR

Para ver os logs do backend em tempo real:

```bash
# No terminal, execute:
docker logs -f audio---transcribe--transcription-service-1
```

**O que procurar:**
```
INFO:app.main:Approve user called by admin for user_id: [uuid]
INFO:app.main:User [username] (id: [uuid]) approved successfully. is_active=True
```

**Se aparecer erro:**
```
ERROR:app.main:User [uuid] not found for approval
```
ou
```
WARNING:app.main:Non-admin user [username] tried to approve user
```

---

## 📊 CHECKLIST DE DIAGNÓSTICO

Marque o que acontece quando você testa:

### Console do Navegador
- [ ] Aparece "approveUser called with id: ..."
- [ ] Aparece "Sending POST to /api/admin/approve/..."
- [ ] Aparece "Response status: 200"
- [ ] Aparece "Success response: ..."
- [ ] Aparece algum erro (qual?)

### Interface
- [ ] Toast verde aparece
- [ ] Usuário some da lista de pendentes
- [ ] Usuário aparece em "Todos os Usuários"
- [ ] Status muda para "Ativo"
- [ ] Nada acontece

### Logs do Servidor
- [ ] Aparece log "Approve user called by admin..."
- [ ] Aparece log "User ... approved successfully"
- [ ] Aparece algum erro (qual?)

---

## 🚨 SE AINDA NÃO FUNCIONAR

**Me envie as seguintes informações:**

1. **Logs do Console do Navegador** (copie e cole tudo que aparecer)
2. **Logs do Servidor** (últimas 20 linhas)
3. **O que acontece** quando clica em "Aprovar":
   - Aparece alguma mensagem?
   - A página recarrega?
   - Nada acontece?

---

## 🔧 COMANDOS ÚTEIS

### Ver logs do servidor em tempo real:
```bash
docker logs -f audio---transcribe--transcription-service-1
```

### Reiniciar servidor:
```bash
docker-compose restart
```

### Verificar se servidor está rodando:
```bash
docker ps
```

---

## 📝 INFORMAÇÕES TÉCNICAS

### Endpoint de Aprovação
- **URL:** `POST /api/admin/approve/{user_id}`
- **Autenticação:** Bearer Token (JWT)
- **Permissão:** Apenas admin
- **Resposta de Sucesso:**
  ```json
  {
    "message": "Usuário aprovado",
    "user_id": "uuid...",
    "username": "nome_do_usuario"
  }
  ```

### Função JavaScript
```javascript
window.approveUser = async (id) => {
    // Envia POST para /api/admin/approve/{id}
    // Recarrega lista de usuários
    // Mostra toast de sucesso
}
```

### Função Backend
```python
@app.post("/api/admin/approve/{user_id}")
async def approve_user(user_id, db, current_user):
    # Verifica se é admin
    # Busca usuário no banco
    # Altera is_active para True
    # Retorna sucesso
```

---

*Guia criado por Antigravity AI - 12/12/2025 12:19*
