#!/usr/bin/env python3
"""
Script para gerar SECRET_KEY para produção Railway
"""
import secrets

print("=" * 60)
print("🔐 SECRET_KEY para Produção Railway")
print("=" * 60)
print()

secret_key = secrets.token_hex(32)

print("Cole esta chave na variável SECRET_KEY do Railway:")
print()
print(f"  {secret_key}")
print()
print("⚠️  IMPORTANTE:")
print("  - Guarde esta chave em local seguro")
print("  - NÃO compartilhe publicamente")
print("  - NÃO commite no git")
print()
print("=" * 60)
