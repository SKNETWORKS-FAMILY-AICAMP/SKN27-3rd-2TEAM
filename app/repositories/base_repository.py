try:
    from psycopg2.extras import RealDictCursor
except ImportError:
    RealDictCursor = None


class BaseRepository:
    def __init__(self, connection):
        self._connection = connection

    def _cursor(self):
        if RealDictCursor is None:
            return self._connection.cursor()
        return self._connection.cursor(cursor_factory=RealDictCursor)
