(() => {
  const te = new TextEncoder();
  const td = new TextDecoder();

  function b64(bytes) {
    let s = "";
    for (let i = 0; i < bytes.length; i += 0x8000) {
      s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    }
    return btoa(s);
  }

  function b64ToBytes(text) {
    const bin = atob(String(text || ""));
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  async function sha256(text) {
    const d = new Uint8Array(await crypto.subtle.digest("SHA-256", te.encode(text)));
    return Array.from(d).map((x) => x.toString(16).padStart(2, "0")).join("");
  }

  function normalizeJwkText(text, label = "Public-Key JWK") {
    let value = String(text || "").trim();
    if (!value) throw new Error(label + " fehlt.");
    for (let i = 0; i < 2; i++) {
      const parsed = JSON.parse(value);
      if (typeof parsed === "string") {
        value = parsed.trim();
        continue;
      }
      if (!parsed || typeof parsed !== "object") {
        throw new Error(label + " ist kein JSON-Objekt.");
      }
      return {jwk: parsed, canonical: JSON.stringify(parsed)};
    }
    throw new Error(label + " konnte nicht gelesen werden.");
  }

  async function generateE2EE() {
    const pair = await crypto.subtle.generateKey({name: "ECDH", namedCurve: "P-256"}, true, ["deriveKey"]);
    const pub = await crypto.subtle.exportKey("jwk", pair.publicKey);
    const priv = await crypto.subtle.exportKey("jwk", pair.privateKey);
    localStorage.setItem("mycelia_e2ee_private_jwk", JSON.stringify(priv));
    localStorage.setItem("mycelia_e2ee_public_jwk", JSON.stringify(pub));

    const pubField = document.getElementById("e2ee-public-key");
    const privField = document.getElementById("e2ee-private-key");
    if (pubField) pubField.value = JSON.stringify(pub);
    if (privField) {
      privField.value = JSON.stringify({
        storage: "browser-localStorage",
        alg: "ECDH-P-256/AES-GCM",
        note: "private key is not sent in plaintext"
      });
    }
    alert("E2EE-Schlüssel erzeugt. Public Key kann jetzt registriert werden.");
  }

  function fillRecipientFromSelect(select) {
    const option = select && select.selectedOptions ? select.selectedOptions[0] : null;
    if (!option || !option.dataset || !option.dataset.recipientSignature) return;

    const sig = document.getElementById("recipient_signature");
    const keySig = document.getElementById("recipient_key_signature");
    const user = document.getElementById("recipient_username");
    const jwk = document.getElementById("recipient_public_key_jwk");
    const hash = document.getElementById("e2ee_recipient_key_hash");
    const allowSelf = document.getElementById("e2ee_allow_self_message");

    if (sig) sig.value = option.dataset.recipientSignature || "";
    if (keySig) keySig.value = option.dataset.recipientKeySignature || option.value || "";
    if (user) user.value = option.dataset.recipientUsername || option.textContent || "";
    if (jwk) jwk.value = option.dataset.publicKeyJwk || "";
    if (hash) hash.value = option.dataset.publicKeyHash || "";
    if (allowSelf) allowSelf.value = option.dataset.allowSelf === "1" ? "1" : "0";

    const form = document.getElementById("e2ee-send-form");
    if (form) form.dataset.e2eeReady = "0";
  }

  async function encryptPayloadFor(publicJwkText, plaintext) {
    const normalized = normalizeJwkText(publicJwkText, "Public-Key JWK");
    if (!normalized.jwk.kty || !normalized.jwk.crv || !normalized.jwk.x || !normalized.jwk.y) {
      throw new Error("Public-Key JWK ist unvollständig.");
    }
    const recipientPub = await crypto.subtle.importKey(
      "jwk",
      normalized.jwk,
      {name: "ECDH", namedCurve: "P-256"},
      false,
      []
    );
    const eph = await crypto.subtle.generateKey({name: "ECDH", namedCurve: "P-256"}, true, ["deriveKey"]);
    const aes = await crypto.subtle.deriveKey(
      {name: "ECDH", public: recipientPub},
      eph.privateKey,
      {name: "AES-GCM", length: 256},
      false,
      ["encrypt"]
    );

    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ephPub = await crypto.subtle.exportKey("jwk", eph.publicKey);
    const aad = "mycelia-e2ee-v1";
    const packed = JSON.stringify({v: 2, plaintext});
    const ct = new Uint8Array(await crypto.subtle.encrypt(
      {name: "AES-GCM", iv, additionalData: te.encode(aad)},
      aes,
      te.encode(packed)
    ));

    return {
      ciphertext_b64: b64(ct),
      nonce_b64: b64(iv),
      eph_public_jwk: JSON.stringify(ephPub),
      public_key_hash: await sha256(normalized.canonical),
      aad
    };
  }

  async function encryptForRecipient(form) {
    const recipientField = document.getElementById("recipient_public_key_jwk");
    const ownPublicField = document.getElementById("sender_public_key_jwk");
    const plaintextField = document.getElementById("e2ee_plaintext");
    const ctField = document.getElementById("e2ee_ciphertext_b64");
    const nonceField = document.getElementById("e2ee_nonce_b64");
    const ephField = document.getElementById("e2ee_eph_public_jwk");
    const hashField = document.getElementById("e2ee_recipient_key_hash");
    const senderCtField = document.getElementById("e2ee_sender_ciphertext_b64");
    const senderNonceField = document.getElementById("e2ee_sender_nonce_b64");
    const senderEphField = document.getElementById("e2ee_sender_eph_public_jwk");
    const senderHashField = document.getElementById("e2ee_sender_key_hash");

    const recipientText = recipientField ? recipientField.value : "";
    const plaintext = plaintextField ? plaintextField.value : "";
    if (!plaintext.trim()) throw new Error("Nachricht fehlt.");

    const main = await encryptPayloadFor(recipientText, plaintext);
    if (ctField) ctField.value = main.ciphertext_b64;
    if (nonceField) nonceField.value = main.nonce_b64;
    if (ephField) ephField.value = main.eph_public_jwk;
    if (hashField && !hashField.value) hashField.value = main.public_key_hash;

    const ownPublic = ownPublicField ? ownPublicField.value : (localStorage.getItem("mycelia_e2ee_public_jwk") || "");
    if (ownPublic && senderCtField && senderNonceField && senderEphField) {
      try {
        const copy = await encryptPayloadFor(ownPublic, plaintext);
        senderCtField.value = copy.ciphertext_b64;
        senderNonceField.value = copy.nonce_b64;
        senderEphField.value = copy.eph_public_jwk;
        if (senderHashField) senderHashField.value = copy.public_key_hash;
      } catch (_) {
        // Sender outbox remains readable only when a current own public key is available.
      }
    }

    form.dataset.e2eeReady = "1";
  }

  async function decryptMessage(button) {
    const card = button.closest("[data-e2ee-message]");
    if (!card) return;
    const out = card.querySelector("[data-e2ee-plaintext]");
    const privText = localStorage.getItem("mycelia_e2ee_private_jwk") || "";
    if (!privText) throw new Error("Kein privater E2EE-Schlüssel in diesem Browser. Erzeuge/verwende den Browser, in dem der Schlüssel registriert wurde.");
    const privJwk = normalizeJwkText(privText, "Private-Key JWK").jwk;
    const ephJwk = normalizeJwkText(card.dataset.ephPublicJwk || "", "Ephemeral Public-Key JWK").jwk;
    const ct = b64ToBytes(card.dataset.ciphertextB64 || "");
    const iv = b64ToBytes(card.dataset.nonceB64 || "");
    if (!ct.length || !iv.length) throw new Error("Ciphertext/Nonce fehlt.");

    const privateKey = await crypto.subtle.importKey(
      "jwk",
      privJwk,
      {name: "ECDH", namedCurve: "P-256"},
      false,
      ["deriveKey"]
    );
    const ephPublic = await crypto.subtle.importKey(
      "jwk",
      ephJwk,
      {name: "ECDH", namedCurve: "P-256"},
      false,
      []
    );
    const aes = await crypto.subtle.deriveKey(
      {name: "ECDH", public: ephPublic},
      privateKey,
      {name: "AES-GCM", length: 256},
      false,
      ["decrypt"]
    );
    const aad = card.dataset.aad || "mycelia-e2ee-v1";
    const plainBytes = await crypto.subtle.decrypt(
      {name: "AES-GCM", iv, additionalData: te.encode(aad)},
      aes,
      ct
    );
    const decoded = td.decode(new Uint8Array(plainBytes));
    let message = decoded;
    try {
      const obj = JSON.parse(decoded);
      message = String(obj.plaintext ?? decoded);
    } catch (_) {}
    if (out) {
      out.textContent = message;
      out.hidden = false;
    }
  }

  function prepareReply(button) {
    const card = button.closest("[data-e2ee-message]");
    if (!card) return;
    const senderSignature = card.dataset.senderSignature || "";
    const senderUsername = card.dataset.senderUsername || "";
    const select = document.getElementById("e2ee-recipient-select");
    if (select && senderSignature) {
      const option = Array.from(select.options).find((opt) => opt.dataset && opt.dataset.recipientSignature === senderSignature);
      if (option) {
        select.value = option.value;
        fillRecipientFromSelect(select);
      }
    }
    const text = document.getElementById("e2ee_plaintext");
    if (text) {
      text.focus();
      text.value = senderUsername ? `@${senderUsername} ` : "";
    }
    const compose = document.getElementById("e2ee-compose");
    if (compose) compose.scrollIntoView({behavior: "smooth", block: "start"});
  }

  document.addEventListener("click", (ev) => {
    const target = ev.target;
    if (target && target.id === "e2ee-generate") {
      generateE2EE().catch((e) => alert(e.message || e));
      return;
    }
    if (target && target.matches("[data-e2ee-decrypt]")) {
      decryptMessage(target).catch((e) => alert("Entschlüsselung fehlgeschlagen: " + (e.message || e)));
      return;
    }
    if (target && target.matches("[data-e2ee-reply]")) {
      prepareReply(target);
    }
  });

  document.addEventListener("change", (ev) => {
    if (ev.target && ev.target.id === "e2ee-recipient-select") {
      fillRecipientFromSelect(ev.target);
    }
  });

  document.addEventListener("input", (ev) => {
    if (ev.target && (ev.target.id === "e2ee_plaintext" || ev.target.id === "recipient_public_key_jwk")) {
      const form = document.getElementById("e2ee-send-form");
      if (form) form.dataset.e2eeReady = "0";
    }
  });

  document.addEventListener("submit", async (ev) => {
    const form = ev.target;
    if (!(form instanceof HTMLFormElement) || form.id !== "e2ee-send-form" || form.dataset.e2eeReady === "1") return;
    ev.preventDefault();
    ev.stopImmediatePropagation();
    try {
      await encryptForRecipient(form);
      form.requestSubmit();
    } catch (e) {
      form.dataset.e2eeReady = "0";
      alert("E2EE-Verschlüsselung fehlgeschlagen: " + (e.message || e));
    }
  }, true);
})();
