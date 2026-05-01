(() => {
  "use strict";

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "readonly");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand("copy");
      return Promise.resolve();
    } catch (err) {
      return Promise.reject(err);
    } finally {
      area.remove();
    }
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".md-copy-code");
    if (!button) return;
    const block = button.closest(".md-codeblock");
    const code = block ? block.querySelector("pre code") : null;
    if (!code) return;

    const original = button.textContent || "Kopieren";
    copyText(code.textContent || "").then(() => {
      button.textContent = "Kopiert";
      button.classList.add("copied");
      setTimeout(() => {
        button.textContent = original;
        button.classList.remove("copied");
      }, 1300);
    }).catch(() => {
      button.textContent = "Fehler";
      setTimeout(() => { button.textContent = original; }, 1300);
    });
  });
})();
