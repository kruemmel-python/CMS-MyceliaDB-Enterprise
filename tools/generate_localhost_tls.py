#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import ipaddress

ROOT = Path(__file__).resolve().parents[1]
key_path = ROOT / "html" / "keys" / "localhost_key.pem"
cert_path = ROOT / "html" / "keys" / "localhost_cert.pem"
key_path.parent.mkdir(parents=True, exist_ok=True)

key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "MyceliaDB Localhost Transport"),
])
cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.now(timezone.utc) - timedelta(minutes=1))
    .not_valid_after(datetime.now(timezone.utc) + timedelta(days=30))
    .add_extension(x509.SubjectAlternativeName([
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ]), critical=False)
    .sign(key, hashes.SHA256())
)
key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
print(cert_path)
print(key_path)
