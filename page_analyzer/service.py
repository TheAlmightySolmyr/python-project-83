from psycopg2.pool import SimpleConnectionPool


class DbManager:
    def __init__(self, db_url):
        self.pool = SimpleConnectionPool(1, 1, db_url)

    def execute(self, query, params=()):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.pool.putconn(conn)

    def fetch_one(self, query, params=()):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.fetchone()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.pool.putconn(conn)

    def fetch_all(self, query, params=()):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.fetchall()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.pool.putconn(conn)

    # запасная универсальная функция
    #
    # def executioner(self, query, params=None, fetch_one=False, fetch_all=False):
    #     conn = self.pool.getconn()
    #     try:
    #         with conn.cursor() as cursor:
    #             cursor.execute(query, params)
    #             conn.commit()
    #             if fetch_one and fetch_all:
    #                 return 'Нельзя использовать fetch_one и fetch_all одновременно'
    #             if fetch_one:
    #                 return cursor.fetchone()
    #             if fetch_all:
    #                 return cursor.fetchall()
    #     except Exception as e:
    #         conn.rollback()
    #         raise e
    #     finally:
    #         self.pool.putconn(conn)
