"""PostgreSQL pgvector sink."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from quicketl.sinks.vector.base import AbstractVectorSink


class PgVectorSink(BaseModel, AbstractVectorSink):
    """Vector store sink for PostgreSQL with pgvector extension.

    Attributes:
        connection_string: PostgreSQL connection string.
        table: Table name for vectors.
        id_column: Column containing vector IDs.
        vector_column: Column containing embeddings.
        metadata_columns: Columns to include as metadata.
        upsert: If True, use ON CONFLICT to update existing rows.
        batch_size: Number of vectors per insert batch.
    """

    connection_string: str = Field(..., description="PostgreSQL connection string")
    table: str = Field(..., description="Table name")
    id_column: str = Field(..., description="Column containing vector IDs")
    vector_column: str = Field(..., description="Column containing embeddings")
    metadata_columns: list[str] = Field(
        default_factory=list,
        description="Columns to include",
    )
    upsert: bool = Field(default=False, description="Use upsert mode")
    batch_size: int = Field(default=100, description="Rows per batch", gt=0)

    model_config = {"extra": "forbid"}

    def write(self, data: list[dict[str, Any]]) -> None:
        """Write vectors to PostgreSQL with pgvector.

        Args:
            data: List of dicts with id, vector, and optional metadata.
        """
        import psycopg2

        conn = psycopg2.connect(self.connection_string)
        cursor = conn.cursor()

        try:
            # Build column list
            columns = [self.id_column, self.vector_column] + self.metadata_columns

            for i in range(0, len(data), self.batch_size):
                batch = data[i : i + self.batch_size]

                for row in batch:
                    values = [
                        str(row[self.id_column]),
                        row[self.vector_column],
                    ]
                    values.extend(row.get(col) for col in self.metadata_columns)

                    # Build SQL
                    placeholders = ", ".join(["%s"] * len(columns))
                    col_names = ", ".join(columns)

                    if self.upsert:
                        # Build update clause for upsert
                        update_cols = [
                            f"{col} = EXCLUDED.{col}"
                            for col in columns
                            if col != self.id_column
                        ]
                        update_clause = ", ".join(update_cols)

                        sql = f"""
                            INSERT INTO {self.table} ({col_names})
                            VALUES ({placeholders})
                            ON CONFLICT ({self.id_column})
                            DO UPDATE SET {update_clause}
                        """
                    else:
                        sql = f"""
                            INSERT INTO {self.table} ({col_names})
                            VALUES ({placeholders})
                        """

                    cursor.execute(sql, values)

            conn.commit()
        finally:
            cursor.close()
            conn.close()
