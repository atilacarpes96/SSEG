// ==UserScript==
// @name         SOL - Entrar sozinho
// @namespace    atilacarpes
// @version      1.0
// @description  Na tela de login do SOE (SOL-CBMRS): preenche a Organização e clica em Entrar depois que o Chrome preencher matrícula e senha. A senha NUNCA fica neste arquivo.
// @match        https://www.soe.rs.gov.br/soeauth/*
// @match        https://soe.rs.gov.br/soeauth/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(function () {
  "use strict";

  // ===== AJUSTE AQUI =====
  // Sigla da organização que você usa no login do SOL (não é segredo). Ex.: "CBM".
  const ORGANIZACAO = "cbm";
  // Segundos esperando o Chrome preencher matrícula e senha.
  const ESPERA = 15;
  // Contagem regressiva antes de clicar em Entrar (clique no aviso para cancelar).
  const CONTAGEM = 5;
  // =======================

  // Só na tela de login que leva ao SOL.
  if (!location.href.includes("solcbm") && !document.referrer.includes("solcbm")) return;

  const org = document.getElementById("organizacao");
  const mat = document.getElementById("matricula");
  const senha = document.getElementById("senha");
  const entrar = document.getElementById("btnLogonOrganizacao");
  if (!org || !mat || !senha || !entrar) return;

  // Uma tentativa automática por aba. Se o SOE recusar a senha, não fica tentando
  // de novo (várias tentativas erradas podem bloquear a conta).
  if (sessionStorage.getItem("solEntrarTentou")) {
    aviso("Já tentei entrar uma vez nesta aba. Confira os campos e clique em Entrar.");
    return;
  }

  function aviso(texto) {
    let el = document.getElementById("solEntrarAviso");
    if (!el) {
      el = document.createElement("div");
      el.id = "solEntrarAviso";
      el.style.cssText =
        "position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:99999;" +
        "background:#b71c1c;color:#fff;padding:10px 16px;border-radius:6px;" +
        "font:15px sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.4)";
      document.body.appendChild(el);
    }
    el.textContent = "SOL Entrar: " + texto;
  }

  function preencher(campo, valor) {
    campo.value = valor;
    campo.dispatchEvent(new Event("input", { bubbles: true }));
    campo.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // O Chrome esconde do script o valor da senha preenchida sozinha até a primeira
  // interação; por isso conta também o estado ":autofill" do campo.
  function preenchido(campo) {
    if (campo.value) return true;
    try { return campo.matches(":autofill"); } catch (e) {}
    try { return campo.matches(":-webkit-autofill"); } catch (e) {}
    return false;
  }

  function contagem() {
    let resta = CONTAGEM;
    let cancelado = false;
    const el = document.getElementById("solEntrarAviso");
    el.style.cursor = "pointer";
    el.onclick = () => {
      cancelado = true;
      clearInterval(t);
      el.style.background = "#555";
      el.textContent = "SOL Entrar: cancelado. Clique em Entrar quando quiser.";
    };
    const mostrar = () => aviso("entrando em " + resta + " s (clique aqui para cancelar)");
    mostrar();
    const t = setInterval(() => {
      resta -= 1;
      if (cancelado) return;
      if (resta > 0) return mostrar();
      clearInterval(t);
      if (!senha.value) return aviso("a senha sumiu do campo. Clique em Entrar você mesmo.");
      sessionStorage.setItem("solEntrarTentou", "1");
      aviso("entrando...");
      entrar.click();
    }, 1000);
  }

  if (ORGANIZACAO === "COLOQUE_AQUI") {
    aviso("abra o Tampermonkey e coloque a sua organização no script.");
    return;
  }
  if (!org.value) preencher(org, ORGANIZACAO);

  let passou = 0;
  aviso("esperando o Chrome preencher matrícula e senha...");
  const timer = setInterval(() => {
    passou += 0.5;
    if (preenchido(mat) && preenchido(senha)) {
      clearInterval(timer);
      if (senha.value) return contagem();
      // O Chrome só entrega a senha preenchida depois de um clique do usuário na página.
      aviso("clique em qualquer lugar da página para liberar a senha");
      const aoClicar = () => setTimeout(() => {
        if (!senha.value) return; // ainda escondida: espera o próximo clique
        document.removeEventListener("pointerdown", aoClicar, true);
        contagem();
      }, 300);
      document.addEventListener("pointerdown", aoClicar, true);
    } else if (passou >= ESPERA) {
      clearInterval(timer);
      aviso("o Chrome não preencheu. Clique no campo Matrícula, escolha a senha salva e clique em Entrar.");
    }
  }, 500);
})();
