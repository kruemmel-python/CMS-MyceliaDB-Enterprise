(() => {
  const te = new TextEncoder();

  function b64(bytes) {
    let s = "";
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      s += String.fromCharCode(...bytes.subarray(i, i + chunk));
    }
    return btoa(s);
  }

  function b64ToBytes(text) {
    const bin = atob(text);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  async function getManifest(op) {
    // Enterprise token broker: fetch a fresh one-time form token immediately
    // before every seal. Never cache the manifest in-page; any read, tab or
    // prior form may have rotated the engine attractor.
    const url = "ingest_manifest.php" + (op ? "?op=" + encodeURIComponent(op) : "");
    const res = await fetch(url, {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      headers: {"Accept": "application/json", "Cache-Control": "no-store"}
    });
    const data = await res.json();
    if (data.status !== "ok") throw new Error(data.message || "Direct-Ingest manifest unavailable");
    return data;
  }

  async function importRsaPublicKey(spkiB64) {
    return crypto.subtle.importKey(
      "spki",
      b64ToBytes(spkiB64),
      {name: "RSA-OAEP", hash: "SHA-256"},
      false,
      ["encrypt"]
    );
  }

  async function fileToB64(file) {
    const buf = new Uint8Array(await file.arrayBuffer());
    return b64(buf);
  }

  async function sha256Hex(text) {
    const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", te.encode(text)));
    return Array.from(digest).map(b => b.toString(16).padStart(2, "0")).join("");
  }

  async function derivePublicMarkdownVaultKey(salt) {
    // Public display vault: prevents PHP/server plaintext materialization for public
    // Markdown. This is not E2EE; it is a client-side rendering vault for public content.
    const material = "myceliadb-public-markdown-vault-v1|" + location.origin;
    const baseKey = await crypto.subtle.importKey("raw", te.encode(material), "PBKDF2", false, ["deriveKey"]);
    return crypto.subtle.deriveKey(
      {name: "PBKDF2", hash: "SHA-256", salt, iterations: 120000},
      baseKey,
      {name: "AES-GCM", length: 256},
      false,
      ["encrypt"]
    );
  }

  async function makeMarkdownVault(field, value, op) {
    const plaintext = String(value || "");
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const aad = "myceliadb-client-markdown-vault-v1|" + op + "|" + field;
    const key = await derivePublicMarkdownVaultKey(salt);
    const ciphertext = new Uint8Array(await crypto.subtle.encrypt(
      {name: "AES-GCM", iv, additionalData: te.encode(aad)},
      key,
      te.encode(plaintext)
    ));
    return {
      version: "client_markdown_vault_v1",
      alg: "PBKDF2-SHA256/AES-256-GCM",
      field,
      markdown: true,
      display_vault: true,
      aad,
      salt_b64: b64(salt),
      iv_b64: b64(iv),
      ciphertext_b64: b64(ciphertext),
      sha256: await sha256Hex(plaintext),
      created_at_ms: Date.now()
    };
  }

  async function vaultPublicMarkdownFields(op, payload) {
    if (!crypto.subtle) return payload;
    const fieldsByOp = {
      create_forum_thread: ["body"],
      update_forum_thread: ["body"],
      create_comment: ["body"],
      update_comment: ["body"],
      create_blog: ["description"],
      update_blog: ["description"],
      create_blog_post: ["body"],
      update_blog_post: ["body"]
    };
    const fields = fieldsByOp[op] || [];
    if (!fields.length) return payload;
    const out = {...payload};
    for (const field of fields) {
      if (!Object.prototype.hasOwnProperty.call(out, field)) continue;
      const value = String(out[field] || "");
      if (!value) continue;
      out[`${field}_vault_json`] = JSON.stringify(await makeMarkdownVault(field, value, op));
      delete out[field];
    }
    return out;
  }



  async function derivePfsAesKey(manifest, salt) {
    const engineRaw = b64ToBytes(manifest.pfs_engine_public_key_raw_b64 || "");
    const enginePublic = await crypto.subtle.importKey(
      "raw",
      engineRaw,
      {name: "X25519"},
      false,
      []
    );
    const clientKey = await crypto.subtle.generateKey({name: "X25519"}, true, ["deriveBits"]);
    const sharedBits = await crypto.subtle.deriveBits({name: "X25519", public: enginePublic}, clientKey.privateKey, 256);
    const hkdfKey = await crypto.subtle.importKey("raw", sharedBits, "HKDF", false, ["deriveKey"]);
    const aesKey = await crypto.subtle.deriveKey(
      {name: "HKDF", hash: "SHA-256", salt, info: te.encode("myceliadb-direct-ingest-pfs-v2")},
      hkdfKey,
      {name: "AES-GCM", length: 256},
      false,
      ["encrypt"]
    );
    const clientPublicRaw = new Uint8Array(await crypto.subtle.exportKey("raw", clientKey.publicKey));
    return {aesKey, clientPublicRaw};
  }

  async function collectPayload(form, submitter) {
    const payload = {};
    const data = new FormData(form);
    for (const [key, value] of data.entries()) {
      if (!key || key === "sealed_ingest" || key === "direct_op") continue;
      const el = form.querySelector(`[name="${CSS.escape(key)}"]`);
      if (el && el.dataset && el.dataset.noIngest === "1") continue;

      if (value instanceof File) {
        if (!value || !value.name || value.size === 0) continue;
        const maxBytes = Number((el && el.dataset && el.dataset.maxBytes) || 3145728);
        if (value.size > maxBytes) throw new Error(`Mediendatei zu groß (${value.size} Bytes, max ${maxBytes}).`);
        const prefix = (el && el.dataset && el.dataset.mediaPrefix) ? el.dataset.mediaPrefix : "media";
        payload[`${prefix}_file_b64`] = await fileToB64(value);
        payload[`${prefix}_file_name`] = value.name;
        payload[`${prefix}_mime`] = value.type || "application/octet-stream";
        payload[`${prefix}_size_bytes`] = String(value.size);
        continue;
      }

      const normalizedKey = key.endsWith("[]") ? key.slice(0, -2) : key;
      if (Object.prototype.hasOwnProperty.call(payload, normalizedKey)) {
        if (Array.isArray(payload[normalizedKey])) payload[normalizedKey].push(String(value));
        else payload[normalizedKey] = [payload[normalizedKey], String(value)];
      } else {
        payload[normalizedKey] = String(value);
      }
    }
    if (submitter && submitter.name) {
      payload[submitter.name] = submitter.value || "1";
    }
    return payload;
  }

  async function seal(op, payload) {
    const manifest = await getManifest(op);
    if (!manifest.allowed_ops || !manifest.allowed_ops.includes(op)) {
      throw new Error(`Direct-Ingest op not allowed: ${op}`);
    }
    const boundPayload = {...payload};
    if (manifest.engine_request_token) {
      boundPayload.__mycelia_request_token = manifest.engine_request_token;
    }
    const body = {
      op,
      issued_at_ms: Date.now(),
      nonce: b64(crypto.getRandomValues(new Uint8Array(18))),
      payload: boundPayload
    };

    if (manifest.pfs && manifest.pfs_engine_public_key_raw_b64 && crypto.subtle) {
      try {
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const salt = crypto.getRandomValues(new Uint8Array(16));
        const {aesKey, clientPublicRaw} = await derivePfsAesKey(manifest, salt);
        const aad = "myceliadb-direct-ingest-pfs-v2";
        const ciphertext = new Uint8Array(await crypto.subtle.encrypt(
          {name: "AES-GCM", iv, additionalData: te.encode(aad)},
          aesKey,
          te.encode(JSON.stringify(body))
        ));
        return {
          v: 2,
          alg: "X25519-HKDF-SHA256/AES-256-GCM",
          aad,
          salt_b64: b64(salt),
          client_ephemeral_public_key_b64: b64(clientPublicRaw),
          iv_b64: b64(iv),
          ciphertext_b64: b64(ciphertext)
        };
      } catch (err) {
        console.warn("PFS Direct-Ingest unavailable; falling back to RSA-OAEP envelope.", err);
      }
    }

    const publicKey = await importRsaPublicKey(manifest.public_key_spki_b64);
    const aesKey = await crypto.subtle.generateKey({name: "AES-GCM", length: 256}, true, ["encrypt"]);
    const rawAes = new Uint8Array(await crypto.subtle.exportKey("raw", aesKey));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const aad = "myceliadb-direct-ingest-v1";
    const ciphertext = new Uint8Array(await crypto.subtle.encrypt(
      {name: "AES-GCM", iv, additionalData: te.encode(aad)},
      aesKey,
      te.encode(JSON.stringify(body))
    ));
    const encryptedKey = new Uint8Array(await crypto.subtle.encrypt(
      {name: "RSA-OAEP", label: te.encode(aad)},
      publicKey,
      rawAes
    ));
    return {
      v: 1,
      alg: "RSA-OAEP-3072-SHA256/AES-256-GCM",
      aad,
      key_b64: b64(encryptedKey),
      iv_b64: b64(iv),
      ciphertext_b64: b64(ciphertext)
    };
  }

  function ensureHidden(form, name) {
    let el = form.querySelector(`input[type="hidden"][name="${name}"]`);
    if (!el) {
      el = document.createElement("input");
      el.type = "hidden";
      el.name = name;
      form.appendChild(el);
    }
    return el;
  }

  function disablePlainFields(form) {
    for (const el of Array.from(form.elements)) {
      if (!el.name || el.name === "sealed_ingest" || el.name === "direct_op") continue;
      if (el.dataset && el.dataset.keepName === "1") continue;
      el.dataset.originalName = el.name;
      el.removeAttribute("name");
    }
  }

  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.matches("form[data-direct-op]")) return;
    // E2EE send forms must first synthesize ciphertext_b64/nonce_b64 in e2ee.js.
    // Direct-Ingest deliberately waits until e2ee.js re-submits with e2eeReady=1.
    if (form.id === "e2ee-send-form" && form.dataset.e2eeReady !== "1") return;
    if (form.dataset.directSealed === "1") return;

    event.preventDefault();
    const button = event.submitter;
    const op = (button && button.dataset && button.dataset.directOp) ? button.dataset.directOp : form.dataset.directOp;

    try {
      const payload = await vaultPublicMarkdownFields(op, await collectPayload(form, button));
      const envelope = await seal(op, payload);
      ensureHidden(form, "direct_op").value = op;
      ensureHidden(form, "sealed_ingest").value = JSON.stringify(envelope);
      form.dataset.directSealed = "1";
      disablePlainFields(form);
      form.submit();
    } catch (err) {
      console.error(err);
      alert("Direct GPU Ingest konnte das Formular nicht versiegeln: " + (err && err.message ? err.message : err));
    }
  }, true);
})();
