"""
database.py
Salva e consulta vagas usando SQLite.
Tecnologias: sqlite3, pandas, SQL (modelagem relacional)
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "vagas.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_tables() -> None:
    """Cria o schema do banco caso não exista."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS fontes (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                nome    TEXT NOT NULL UNIQUE,
                url     TEXT
            );

            CREATE TABLE IF NOT EXISTS vagas (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo       TEXT NOT NULL,
                empresa      TEXT,
                link         TEXT,
                descricao    TEXT,
                categoria    TEXT,
                score_ia     REAL,
                fonte_id     INTEGER REFERENCES fontes(id),
                coletado_em  TEXT
            );
        """)
    print("✅ Tabelas criadas com sucesso.")


def insert_vagas(df: pd.DataFrame) -> None:
    """Insere DataFrame de vagas no banco, evitando duplicatas."""
    with get_connection() as conn:
        for _, row in df.iterrows():
            # upsert simples por titulo + empresa
            existing = conn.execute(
                "SELECT id FROM vagas WHERE titulo = ? AND empresa = ?",
                (row["titulo"], row.get("empresa", ""))
            ).fetchone()

            if not existing:
                conn.execute("""
                    INSERT INTO vagas (titulo, empresa, link, descricao, categoria, score_ia, coletado_em)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("titulo"),
                    row.get("empresa"),
                    row.get("link"),
                    row.get("descricao"),
                    row.get("categoria"),
                    row.get("score_ia"),
                    row.get("coletado_em"),
                ))
    print(f"✅ {len(df)} vagas processadas.")


def query_vagas(categoria: str = None, limit: int = 50) -> pd.DataFrame:
    """Consulta vagas com filtro opcional por categoria."""
    with get_connection() as conn:
        if categoria:
            query = "SELECT * FROM vagas WHERE categoria = ? ORDER BY coletado_em DESC LIMIT ?"
            return pd.read_sql_query(query, conn, params=(categoria, limit))
        else:
            return pd.read_sql_query(
                f"SELECT * FROM vagas ORDER BY coletado_em DESC LIMIT {limit}", conn
            )


def stats() -> dict:
    """Retorna estatísticas básicas do banco."""
    with get_connection() as conn:
        total     = conn.execute("SELECT COUNT(*) FROM vagas").fetchone()[0]
        por_cat   = pd.read_sql_query(
            "SELECT categoria, COUNT(*) as total FROM vagas GROUP BY categoria", conn
        )
    return {"total": total, "por_categoria": por_cat}


if __name__ == "__main__":
    create_tables()
    print(stats())
