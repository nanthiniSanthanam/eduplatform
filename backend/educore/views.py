from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError
import time


@api_view(['GET'])
def db_status(request):
    """Return database connection status."""
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT 1")
            return Response({"status": "connected"})
    except (OperationalError, ProgrammingError):
        return Response({"status": "disconnected"}, status=503)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def db_stats(request):
    """Return database statistics for admin users."""
    try:
        stats = {}
        with connections['default'].cursor() as cursor:
            # Database size
            cursor.execute(
                "SELECT pg_size_pretty(pg_database_size(current_database()))")
            stats['database_size'] = cursor.fetchone()[0]

            # Connection count
            cursor.execute("""
                SELECT count(*) FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            stats['active_connections'] = cursor.fetchone()[0]

            # Table statistics
            cursor.execute("""
                SELECT relname, n_live_tup, pg_size_pretty(pg_relation_size(quote_ident(relname)::text))
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
                LIMIT 10
            """)
            tables = cursor.fetchall()
            stats['tables'] = [
                {
                    'name': table[0],
                    'rows': table[1],
                    'size': table[2]
                }
                for table in tables
            ]

            return Response(stats)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
