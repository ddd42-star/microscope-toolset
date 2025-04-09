import os
import logging
from typing import Optional, List
from src.postqrl.connection import DBConnection

logger = logging.getLogger(__name__)
from psycopg2.extras import Json


class LoggerDB:

    def __init__(self, connection: DBConnection):
        self.connection = connection

        # activate vector extension
        self.initialize()

    def initialize(self):
        connection = self.connection.get_connect()

        try:
            with connection.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector; -- doing a vector search")
                print("Vector extension was activated")
        except Exception as e:
            logger.error(e)
        finally:
            self.connection.put_connect(connection)

    def list_collection(self):
        connection = self.connection.get_connect()
        try:
            with connection.cursor() as cur:
                cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """)

                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(e)
        finally:
            self.connection.put_connect(connection)

    def create_collection(self, collection_name: str):
        connection = self.connection.get_connect()
        # verify that the name doesn't exits already
        if collection_name in self.list_collection():
            logger.error("The database contains already a collection called %s", collection_name)
        try:
            with connection.cursor() as cur:
                cur.execute(f"""
                CREATE TABLE {collection_name}(
                id SERIAL PRIMARY KEY,
                prompt TEXT NOT NULL,
                output TEXT NOT NULL,
                feedback BOOLEAN,
                category TEXT,
                embedding VECTOR(512),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
                );
                """)
                connection.commit()
                logger.info(f"The collection {collection_name} was created successfully")
        except Exception as e:
            logger.error(e)

        finally:
            self.connection.put_connect(connection)

    def get_collection(self, collection_name: str):
        connection = self.connection.get_connect()

        if collection_name not in self.list_collection():
            logger.error(f"The collection {collection_name} doesn't exist or is not present into the database.")

        try:
            with connection.cursor() as cur:

                cur.execute(f"""
                SELECT * FROM {collection_name}
                """)

                return [
                    {"prompt": row[1], "output": row[2], "feedback": row[3], "category": row[4], "embedding": row[5]}
                    for row in cur.fetchall()]
        except Exception as e:
            logger.error(e)
        finally:
            self.connection.put_connect(connection)

    def update_collection(self):
        pass

    def insert(self, collection_name: str, data_dict, embeddings=None):

        connection = self.connection.get_connect()

        if collection_name not in self.list_collection():
            logger.error(f"The collection {collection_name} is not in the database")

        try:

            with connection.cursor() as cur:

                cur.execute(f"""
                INSERT INTO {collection_name}
                (prompt, output, feedback, category, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                data_dict["prompt"], data_dict["output"], data_dict["feedback"], data_dict["category"],
                embeddings, Json(data_dict)))

                connection.commit()

        except Exception as e:
            logger.error(e)
        finally:
            self.connection.put_connect(connection)

    def delete(self, collection_name: str):

        connection = self.connection.get_connect()

        if collection_name not in self.list_collection():
            logger.error(f"The collection {collection_name} is not into the database")

        try:
            with connection.cursor() as cur:
                cur.execute(f"""
                DROP TABLE IF EXISTS {collection_name}
                """)

                logger.info(f"The collection {collection_name} was permanently deleted.")

        except Exception as e:
            logger.error(e)

        finally:
            self.connection.put_connect(connection)


    def query(self):

        pass

    def query_by_category(self, collection_name: str, category: str, k = 10):

        connection = self.connection.get_connect()

        if collection_name not in self.list_collection():
            logger.error(f"The collection {collection_name} is not present into the database")

        try:
            with connection.cursor() as cur:

                cur.execute(f"""
                SELECT * FROM {collection_name} WHERE category = %s LIMIT %s
                """, (category,str(k)))
                return [
                    {"prompt": row[1], "output": row[2], "feedback": row[3], "category": row[4], "embedding": row[5]}
                    for row in cur.fetchall()]

        except Exception as e:
            logger.error(e)
        finally:
            self.connection.put_connect(connection)

    def query_by_vector(self, collection_name: str, vector: List[float], k=10):
        connection = self.connection.get_connect()

        if collection_name not in self.list_collection():
            logger.error(f"The collection {collection_name} is not present into the database")

        try:
            with connection.cursor() as cur:
                cur.execute(f"""
                SELECT prompt, output, feedback, category,
                1 - (embedding <#> %s) AS similarity
                FROM {collection_name}
                ORDER BY similarity DESC
                LIMIT %s
                """, (str(vector), str(k)))

                return [
                    {"prompt": row[1], "output": row[2], "feedback": row[3], "category": row[4], "embedding": row[5]}
                    for row in cur.fetchall()]
        except Exception as e:
            logger.error(e)
        finally:
            self.connection.put_connect(connection)

    def query_feedback(self, collection_name: str, feedback: bool, k = 10):
        connection = self.connection.get_connect()

        if collection_name not in self.list_collection():
            logger.error(f"The collection {collection_name} is not into the database.")
        try:
            with connection.cursor() as cur:
                cur.execute(f"""
                SELECT * FROM {collection_name} WHERE feedback = %s LIMIT %s
                """, (feedback,str(k)))

                return [
                    {"prompt": row[1], "output": row[2], "feedback": row[3], "category": row[4], "embedding": row[5]}
                    for row in cur.fetchall()]
        except Exception as e:
            logger.error(e)

        finally:
            self.connection.put_connect(connection)

