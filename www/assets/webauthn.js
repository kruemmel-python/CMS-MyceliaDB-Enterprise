(() => {
  function b64urlToBytes(s){s=s.replace(/-/g,'+').replace(/_/g,'/'); while(s.length%4)s+='='; const bin=atob(s); const out=new Uint8Array(bin.length); for(let i=0;i<bin.length;i++)out[i]=bin.charCodeAt(i); return out;}
  function b64url(bytes){let str=''; for(let i=0;i<bytes.length;i++)str+=String.fromCharCode(bytes[i]); return btoa(str).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
  async function startRegister(){
    if (!navigator.credentials || !window.PublicKeyCredential) throw new Error('WebAuthn wird von diesem Browser nicht unterstützt.');
    const res = await fetch('webauthn_manifest.php', {credentials:'same-origin', cache:'no-store'});
    const ch = await res.json();
    if(ch.status !== 'ok') throw new Error(ch.message || 'Challenge nicht verfügbar');
    const cred = await navigator.credentials.create({publicKey:{
      challenge: b64urlToBytes(ch.challenge_b64url),
      rp: {name:'MyceliaDB', id: location.hostname},
      user: {id: new TextEncoder().encode('mycelia-user'), name:'mycelia-user', displayName:'Mycelia User'},
      pubKeyCredParams:[{type:'public-key', alg:-7}, {type:'public-key', alg:-257}],
      authenticatorSelection:{userVerification:'preferred'},
      timeout:60000,
      attestation:'none'
    }});
    document.getElementById('webauthn_challenge_id').value = ch.challenge_id;
    document.getElementById('webauthn_credential_id').value = b64url(new Uint8Array(cred.rawId));
    document.getElementById('webauthn_public_key').value = b64url(new Uint8Array(cred.response.attestationObject));
    alert('Credential erzeugt. Jetzt speichern.');
  }
  document.addEventListener('click', ev => {
    if(ev.target && ev.target.id === 'webauthn-register') startRegister().catch(e => alert(e.message||e));
  });
})();
