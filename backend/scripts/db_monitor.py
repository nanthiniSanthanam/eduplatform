#!/usr/bin/env python
"""
Database monitoring script for Educational Platform.
Author: nanthiniSanthanam
Date: 2025-04-21
"""

from django.apps import apps
from django.db import connection, connections
import os
import sys
import django
import time
import json
from datetime import datetime

# Add the project path to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educore.settings')
django.setup()

# Import Django modules


def get_connection_stats():
    """Get database connection statistics."""
    with connection.cursor() as cursor:
        # Get active connections
        cursor.execute("""
            SELECT count(*) FROM pg_stat_activity 
            WHERE datname = current_database()
        """)
        active_connections = cursor.fetchone()[0]

        # Get database size
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """)
        db_size = cursor.fetchone()[0]

        # Get table statistics
        cursor.execute("""
            SELECT relname, n_live_tup, n_dead_tup
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
            LIMIT 10
        """)
        tables = cursor.fetchall()

        # Get recent queries
        cursor.execute("""
            SELECT query, calls, total_time, rows, 
                   100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements
            WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
            ORDER BY total_time DESC
            LIMIT 5
        """)
        queries = cursor.fetchall()

        return {
            'timestamp': datetime.now().isoformat(),
            'active_connections': active_connections,
            'database_size': db_size,
            'tables': [
                {'name': table[0], 'live_rows': table[1],
                    'dead_rows': table[2]}
                for table in tables
            ],
            'top_queries': [
                {
                    'query': query[0][:100] + ('...' if len(query[0]) > 100 else ''),
                    'calls': query[1],
                    'total_time': round(query[2], 2),
                    'rows': query[3],
                    'cache_hit_percent': round(query[4] if query[4] else 0, 2)
                }
                for query in queries
            ] if queries else []
        }


def get_model_stats():
    """Get statistics for each model."""
    model_stats = []
    for model in apps.get_models():
        model_name = f"{model._meta.app_label}.{model._meta.object_name}"
        try:
            count = model.objects.count()
            model_stats.append({
                'model': model_name,
                'count': count
            })
        except Exception as e:
            model_stats.append({
                'model': model_name,
                'error': str(e)
            })

    return model_stats


def run_monitor():
    """Run monitoring and output results."""
    try:
        # Collect statistics
        stats = {
            'connection_stats': get_connection_stats(),
            'model_stats': get_model_stats()
        }

        # Create monitoring directory if it doesn't exist
        os.makedirs('../monitoring', exist_ok=True)

        # Generate report file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'../monitoring/db_report_{timestamp}.json'

        with open(report_file, 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"Monitoring report generated: {report_file}")

        # Output summary to console
        print("\nDatabase Monitoring Summary:")
        print(
            f"Active connections: {stats['connection_stats']['active_connections']}")
        print(f"Database size: {stats['connection_stats']['database_size']}")
        print(f"\nTop 5 tables by row count:")
        for i, table in enumerate(sorted(stats['connection_stats']['tables'], key=lambda x: x['live_rows'], reverse=True)[:5], 1):
            print(f"{i}. {table['name']}: {table['live_rows']} rows")

        return True

    except Exception as e:
        print(f"Monitoring failed: {e}")
        return False


if __name__ == "__main__":
    run_monitor()
