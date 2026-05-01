(() => {
  "use strict";

  const te = new TextEncoder();
  const td = new TextDecoder();

  function b64ToBytes(text) {
    const bin = atob(String(text || ""));
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  async function derivePublicMarkdownVaultKey(salt) {
    const material = "myceliadb-public-markdown-vault-v1|" + location.origin;
    const baseKey = await crypto.subtle.importKey("raw", te.encode(material), "PBKDF2", false, ["deriveKey"]);
    return crypto.subtle.deriveKey(
      {name: "PBKDF2", hash: "SHA-256", salt, iterations: 120000},
      baseKey,
      {name: "AES-GCM", length: 256},
      false,
      ["decrypt"]
    );
  }

  async function decryptVault(vault) {
    if (!vault || vault.version !== "client_markdown_vault_v1") {
      throw new Error("Ungültiges Markdown-Vault-Paket");
    }
    const salt = b64ToBytes(vault.salt_b64);
    const iv = b64ToBytes(vault.iv_b64);
    const ciphertext = b64ToBytes(vault.ciphertext_b64);
    const key = await derivePublicMarkdownVaultKey(salt);
    const plain = await crypto.subtle.decrypt(
      {name: "AES-GCM", iv, additionalData: te.encode(String(vault.aad || ""))},
      key,
      ciphertext
    );
    return td.decode(plain);
  }

  function inlineMarkdown(text) {
    let s = escapeHtml(text);
    s = s.replace(/`([^`\n]+)`/g, (_, code) => `<code>${escapeHtml(code)}</code>`);
    s = s.replace(/\[([^\]\n]{1,160})\]\((https?:\/\/[^\s\)<>"']{1,500})\)/g, (_, label, url) => {
      const safe = escapeHtml(url);
      return `<a href="${safe}" rel="nofollow noopener noreferrer" target="_blank">${escapeHtml(label)}</a>`;
    });
    s = s.replace(/\*\*([^*\n]{1,240})\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(?<!\*)\*([^*\n]{1,180})\*(?!\*)/g, "<em>$1</em>");
    return s;
  }

  function renderMarkdown(source) {
    const lines = String(source || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
    const out = [];
    let paragraph = [];
    let inCode = false;
    let codeLang = "";
    let codeLines = [];

    const flushParagraph = () => {
      if (!paragraph.length) return;
      const joined = paragraph.map(x => x.trim()).filter(Boolean).join(" ");
      if (joined) out.push(`<p>${inlineMarkdown(joined)}</p>`);
      paragraph = [];
    };

    const renderCode = () => {
      const codeText = codeLines.join("\n");
      const lang = String(codeLang || "code").replace(/[^A-Za-z0-9_+-]/g, "").slice(0, 32) || "code";
      out.push(
        `<div class="md-codeblock">` +
        `<div class="md-codebar"><span>${escapeHtml(lang)}</span><button type="button" class="md-copy-code" aria-label="Code kopieren">Kopieren</button></div>` +
        `<pre><code class="language-${escapeHtml(lang)}">${escapeHtml(codeText)}</code></pre>` +
        `</div>`
      );
      codeLang = "";
      codeLines = [];
    };

    for (let i = 0; i < lines.length;) {
      const line = lines[i];
      const stripped = line.trim();

      if (inCode) {
        if (stripped.startsWith("```")) {
          renderCode();
          inCode = false;
        } else {
          codeLines.push(line);
        }
        i++;
        continue;
      }

      if (stripped.startsWith("```")) {
        flushParagraph();
        inCode = true;
        codeLang = stripped.slice(3).trim();
        codeLines = [];
        i++;
        continue;
      }

      if (!stripped) {
        flushParagraph();
        i++;
        continue;
      }

      const heading = /^(#{1,6})\s+(.+)$/.exec(stripped);
      if (heading) {
        flushParagraph();
        const level = Math.min(heading[1].length, 6);
        out.push(`<h${level}>${inlineMarkdown(heading[2].trim())}</h${level}>`);
        i++;
        continue;
      }

      const quote = /^>\s?(.*)$/.exec(stripped);
      if (quote) {
        flushParagraph();
        const q = [];
        while (i < lines.length) {
          const m = /^>\s?(.*)$/.exec(lines[i].trim());
          if (!m) break;
          q.push(`<p>${inlineMarkdown(m[1])}</p>`);
          i++;
        }
        out.push(`<blockquote>${q.join("")}</blockquote>`);
        continue;
      }

      const ul = /^[-*]\s+(.+)$/.exec(stripped);
      const ol = /^\d+[.)]\s+(.+)$/.exec(stripped);
      if (ul || ol) {
        flushParagraph();
        const ordered = Boolean(ol);
        const items = [];
        while (i < lines.length) {
          const candidate = lines[i].trim();
          const m = ordered ? /^\d+[.)]\s+(.+)$/.exec(candidate) : /^[-*]\s+(.+)$/.exec(candidate);
          if (!m) break;
          items.push(`<li>${inlineMarkdown(m[1].trim())}</li>`);
          i++;
        }
        out.push(`<${ordered ? "ol" : "ul"}>${items.join("")}</${ordered ? "ol" : "ul"}>`);
        continue;
      }

      paragraph.push(line);
      i++;
    }

    if (inCode) renderCode();
    flushParagraph();
    return out.join("\n");
  }

  async function hydrateVault(node) {
    try {
      const raw = atob(node.dataset.markdownVault || "");
      const vault = JSON.parse(raw);
      const markdown = await decryptVault(vault);
      node.innerHTML = renderMarkdown(markdown);
      node.classList.add("markdown-vault-ready");
      node.dataset.markdownVaultHydrated = "1";
    } catch (err) {
      console.error("Markdown Vault konnte nicht entschlüsselt werden", err);
      node.innerHTML = `<p class="error">Markdown konnte lokal nicht entschlüsselt werden.</p>`;
      node.classList.add("markdown-vault-error");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (!crypto.subtle) {
      for (const node of document.querySelectorAll(".markdown-vault")) {
        node.innerHTML = `<p class="error">WebCrypto ist erforderlich, um diesen Inhalt lokal zu entschlüsseln.</p>`;
      }
      return;
    }
    for (const node of document.querySelectorAll(".markdown-vault[data-markdown-vault]")) {
      hydrateVault(node);
    }
  });
})();
