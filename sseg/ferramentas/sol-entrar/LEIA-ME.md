# SOL Entrar

Ferramenta para entrar no SOL-CBMRS **sem digitar**, para quando o teclado do PC não funciona. Usa a matrícula e a senha que o gerenciador de senhas do Chrome já guarda. A senha não fica em nenhum destes arquivos.

| Arquivo | O que faz |
|---|---|
| `sol-entrar.user.js` | Script do Tampermonkey. Na tela de login do SOE, preenche a Organização (`cbm`). Quando o Chrome já preencheu matrícula e senha, faz uma contagem de 5 s, que dá para cancelar, e clica em Entrar. Tenta uma vez só por aba e nunca envia a senha vazia. |
| `abrir-sol.ps1` | Abre o SOL no Chrome, espera a tela "Acesso" do SOE e dá um clique numa área vazia da página. A área é achada pela acessibilidade do Windows, então funciona também com abas na vertical e com qualquer escala de tela. O Chrome só entrega a senha preenchida ao script depois de um clique real. Se a janela da frente não for a do login, não clica em nada. |
| `Abrir SOL.bat` | Chama o `.ps1` sem janela. É o alvo do atalho "Abrir SOL" da Área de Trabalho. |

Testado no PC de casa em 12/10/2026: entra com dois cliques no atalho.

## Instalar à mão

1. **Tampermonkey:** instale a extensão no Chrome. Em `chrome://extensions`, ligue o Modo do desenvolvedor e, em Detalhes do Tampermonkey, ligue "Permitir scripts de usuário". Crie um script novo e cole o `sol-entrar.user.js`.
2. **Senha:** faça o login uma vez digitando e salve a senha no Chrome. No PC do trabalho, o Chrome precisa estar logado na mesma conta Google, com a sincronização de senhas ligada.
3. **Atalho:** crie na Área de Trabalho um atalho para o `Abrir SOL.bat`.
