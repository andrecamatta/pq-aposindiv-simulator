"""
Script de migração para adicionar campos de autenticação na tabela User
"""
import sqlite3
from pathlib import Path
import sys

# Adicionar o diretório pai ao path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import DATABASE_DIR


def check_column_exists(cursor, table_name: str, column_name: str) -> bool:
    """Verifica se uma coluna existe em uma tabela"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate_add_auth_fields():
    """Adiciona campos de autenticação na tabela User se não existirem"""
    db_path = DATABASE_DIR / "simulador.db"

    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        print("Execute a aplicação primeiro para criar o banco de dados.")
        return False

    print(f"📦 Conectando ao banco de dados: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verificar se a tabela User existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            print("❌ Tabela 'user' não existe")
            return False

        print("✅ Tabela 'user' encontrada")

        # Lista de colunas para adicionar (sem UNIQUE - será adicionado via índice)
        columns_to_add = [
            ("google_id", "TEXT"),
            ("avatar_url", "TEXT"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("last_login_at", "TIMESTAMP"),
        ]

        added_columns = []
        skipped_columns = []

        for column_name, column_type in columns_to_add:
            if check_column_exists(cursor, "user", column_name):
                print(f"⏭️  Coluna '{column_name}' já existe, pulando...")
                skipped_columns.append(column_name)
            else:
                print(f"➕ Adicionando coluna '{column_name}'...")
                cursor.execute(f"ALTER TABLE user ADD COLUMN {column_name} {column_type}")
                added_columns.append(column_name)

        # Criar índice UNIQUE para google_id (funciona mesmo se a coluna já existia)
        print("📊 Criando índice UNIQUE para google_id...")
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_google_id ON user(google_id)")
        except sqlite3.IntegrityError:
            print("⚠️  Aviso: Não foi possível criar índice UNIQUE (pode haver duplicatas)")

        # Commit das mudanças
        conn.commit()

        print("\n" + "="*60)
        print("✅ Migração concluída com sucesso!")
        print("="*60)

        if added_columns:
            print(f"\n➕ Colunas adicionadas: {', '.join(added_columns)}")

        if skipped_columns:
            print(f"\n⏭️  Colunas já existentes: {', '.join(skipped_columns)}")

        # Mostrar estrutura final da tabela
        print("\n📋 Estrutura atual da tabela 'user':")
        cursor.execute("PRAGMA table_info(user)")
        for row in cursor.fetchall():
            print(f"  - {row[1]}: {row[2]}")

        return True

    except Exception as e:
        print(f"\n❌ Erro durante a migração: {str(e)}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔄 MIGRATION: Adicionar campos de autenticação")
    print("="*60 + "\n")

    success = migrate_add_auth_fields()

    if success:
        print("\n✅ Migração executada com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Migração falhou!")
        sys.exit(1)
