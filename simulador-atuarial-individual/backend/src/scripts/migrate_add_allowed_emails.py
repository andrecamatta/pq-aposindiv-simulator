#!/usr/bin/env python3
"""
Script de migração: Criar tabela allowed_email e popular com emails iniciais

Cria a tabela de whitelist de emails no banco de dados
e adiciona os 3 emails autorizados inicialmente.
"""
import sqlite3
import os
from datetime import datetime

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/simulador.db")

def migrate():
    """Executa a migração"""
    print("=" * 70)
    print("🔐 Migração: Criar tabela allowed_email")
    print("=" * 70)
    print()

    if not os.path.exists(DB_PATH):
        print(f"❌ Erro: Banco de dados não encontrado em {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Verificar se tabela já existe
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='allowedemail'
        """)

        if cursor.fetchone():
            print("⚠️  Tabela 'allowedemail' já existe, pulando criação...")
        else:
            print("📝 Criando tabela 'allowedemail'...")

            # Criar tabela
            cursor.execute("""
                CREATE TABLE allowedemail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP NOT NULL,
                    created_by TEXT,
                    note TEXT
                )
            """)

            # Criar índice
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_allowedemail_email
                ON allowedemail(email)
            """)

            print("✅ Tabela criada com sucesso!")

        # Popular com emails iniciais
        print()
        print("📋 Adicionando emails autorizados iniciais...")

        initial_emails = [
            ("andrecamatta@gmail.com", "Usuário inicial - Admin"),
            ("isabeladpimentel@gmail.com", "Usuário inicial"),
            ("diogobira@gmail.com", "Usuário inicial"),
        ]

        now = datetime.utcnow().isoformat()
        added_count = 0

        for email, note in initial_emails:
            try:
                cursor.execute("""
                    INSERT INTO allowedemail (email, created_at, created_by, note)
                    VALUES (?, ?, ?, ?)
                """, (email, now, "system", note))
                print(f"  ✅ {email}")
                added_count += 1
            except sqlite3.IntegrityError:
                print(f"  ⚠️  {email} (já existe)")

        conn.commit()

        # Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM allowedemail")
        total = cursor.fetchone()[0]

        print()
        print(f"✅ Migração concluída!")
        print(f"   - Emails adicionados: {added_count}")
        print(f"   - Total na whitelist: {total}")
        print()

        # Listar todos os emails
        print("📧 Emails autorizados:")
        cursor.execute("SELECT email, created_at, note FROM allowedemail ORDER BY created_at")
        for row in cursor.fetchall():
            email, created, note = row
            note_str = f" ({note})" if note else ""
            print(f"   - {email}{note_str}")

        print()
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate()
    exit(0 if success else 1)
