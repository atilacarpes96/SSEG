#!/usr/bin/env bash
# Monta o servidor do SSEG numa VM Ubuntu 24.04 (Oracle Cloud Always Free, A1 ARM ou Micro x86).
# Ver sseg/workflow/plano-servidor-24-7.md.
#
# Uso, já conectado por SSH na VM:
#   bash montar.sh
#
# Pode rodar de novo sem estragar nada: cada passo confere se já foi feito.
# Não faz login em nada. Os passos que dependem do Átila são avisados no fim.
set -euo pipefail

REPO_SSH="git@github.com:atilacarpes96/SSEG.git"
PASTA="$HOME/SSEG"

passo() { printf '\n== %s\n' "$1"; }

passo "1/6 Sistema atualizado e fuso de Brasília (as rotinas do cron usam este horário)"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq
sudo timedatectl set-timezone America/Sao_Paulo

passo "2/6 Ferramentas: git, tmux, pdftotext (Poppler), Python, atualização automática de segurança"
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  git tmux poppler-utils python3 python3-pip python3-venv unattended-upgrades curl
# Mesmo motivo do `setx PYTHONUTF8 1` no Windows: a saída do pdftotext é UTF-8.
grep -q PYTHONUTF8 "$HOME/.bashrc" || echo 'export PYTHONUTF8=1' >> "$HOME/.bashrc"

passo "3/6 Chave de deploy do GitHub (só para o repositório SSEG)"
if [ ! -f "$HOME/.ssh/sseg_deploy" ]; then
  ssh-keygen -t ed25519 -f "$HOME/.ssh/sseg_deploy" -N "" -C "sseg-servidor-deploy" -q
fi
if ! grep -q "Host github.com" "$HOME/.ssh/config" 2>/dev/null; then
  cat >> "$HOME/.ssh/config" <<'EOF'
Host github.com
  IdentityFile ~/.ssh/sseg_deploy
  IdentitiesOnly yes
EOF
  chmod 600 "$HOME/.ssh/config"
fi
# Sem -q: o ssh-keyscan do Ubuntu 24.04 nao aceita a opcao e o set -e parava aqui.
grep -q "^github.com " "$HOME/.ssh/known_hosts" 2>/dev/null || ssh-keyscan github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null

passo "4/6 Clone do SSEG"
if [ -d "$PASTA/.git" ]; then
  echo "já existe em $PASTA"
elif ssh -o BatchMode=yes -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
  git clone -q "$REPO_SSH" "$PASTA"
  mkdir -p "$PASTA/sseg/processos"
  echo "clonado em $PASTA"
else
  echo "PENDENTE: a chave de deploy ainda não foi cadastrada no GitHub (ver o fim)."
fi

passo "5/6 Claude Code (instalador oficial; ele escolhe ARM64 ou x86)"
if ! command -v claude >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/claude" ]; then
  curl -fsSL https://claude.ai/install.sh | bash
fi
grep -q '.local/bin' "$HOME/.bashrc" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"

passo "6/6 Conferência"
printf 'git %s | tmux %s | %s | %s\n' \
  "$(git --version | awk '{print $3}')" "$(tmux -V | awk '{print $2}')" \
  "$(pdftotext -v 2>&1 | head -1)" "$(python3 --version)"
"$HOME/.local/bin/claude" --version 2>/dev/null || echo "claude: abra um terminal novo e rode 'claude --version'"

cat <<EOF

------------------------------------------------------------------
FALTA O ÁTILA:

1. Cadastrar a chave de deploy no GitHub:
   github.com/atilacarpes96/SSEG -> Settings -> Deploy keys -> Add deploy key
   Título: servidor-oracle. Marcar "Allow write access". Colar:

$(cat "$HOME/.ssh/sseg_deploy.pub")

   Depois rodar este script de novo para clonar.

2. Login do Claude pela assinatura (não por API):
   cd $PASTA && claude
   Abrir o link que aparecer no navegador e colar o código de volta.

3. Sessão fixa com acesso pelo app:
   tmux new -s sseg   (dentro: cd $PASTA && claude, depois /remote-control)
------------------------------------------------------------------
EOF
