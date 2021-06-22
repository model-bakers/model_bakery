from django.db import connection


class QueryCount:
    """
    Keep track of db calls.

    Example:
    ========

        qc = QueryCount()

        with qc.start_count():
            MyModel.objects.get(pk=1)
            MyModel.objects.create()

        qc.count  # 2

    """

    def __init__(self):
        self.count = 0

    def __call__(self, execute, sql, params, many, context):
        """
        `django.db.connection.execute_wrapper` callback.

        https://docs.djangoproject.com/en/3.1/topics/db/instrumentation/
        """
        self.count += 1
        execute(sql, params, many, context)

    def start_count(self):
        """Reset query count to 0 and return context manager for wrapping db queries."""
        self.count = 0

        return connection.execute_wrapper(self)
