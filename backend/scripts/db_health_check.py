from django.conf import settings
from django.db import connection
import os
import sys
import django
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educore.settings')
django.setup()

# Import Django modules


def run_health_check(send_email=False, email_recipient=None):
    """Run database health checks."""

    results = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'issues': [],
        'checks': []
    }

    # Check 1: Database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            results['checks'].append({
                'name': 'connectivity',
                'status': 'passed',
                'message': 'Successfully connected to database'
            })
    except Exception as e:
        results['status'] = 'critical'
        results['issues'].append(f"Cannot connect to database: {str(e)}")
        results['checks'].append({
            'name': 'connectivity',
            'status': 'failed',
            'message': str(e)
        })

    # Check 2: Connection count (too many connections might indicate a leak)
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            count = cursor.fetchone()[0]
            results['checks'].append({
                'name': 'connection_count',
                'status': 'passed' if count < 80 else 'warning',
                'message': f"{count} active connections",
                'value': count
            })
            if count >= 80:
                results['status'] = 'warning'
                results['issues'].append(
                    f"High number of connections: {count}")
    except Exception as e:
        results['checks'].append({
            'name': 'connection_count',
            'status': 'error',
            'message': f"Error checking connections: {str(e)}"
        })

    # Check 3: Long-running queries
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE datname = current_database()
                  AND state = 'active'
                  AND (now() - query_start) > interval '30 seconds'
            """)
            count = cursor.fetchone()[0]
            results['checks'].append({
                'name': 'long_queries',
                'status': 'passed' if count == 0 else 'warning',
                'message': f"{count} queries running longer than 30 seconds",
                'value': count
            })
            if count > 0:
                results['status'] = 'warning'
                results['issues'].append(
                    f"{count} long-running queries detected")
    except Exception as e:
        results['checks'].append({
            'name': 'long_queries',
            'status': 'error',
            'message': f"Error checking long queries: {str(e)}"
        })

    # Check 4: Disk usage
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT pg_database_size(current_database()) / (1024*1024) as size_mb
            """)
            size_mb = cursor.fetchone()[0]
            results['checks'].append({
                'name': 'disk_usage',
                'status': 'passed' if size_mb < 10000 else 'warning',  # Warning if > 10GB
                'message': f"Database size: {size_mb:.2f} MB",
                'value': size_mb
            })
    except Exception as e:
        results['checks'].append({
            'name': 'disk_usage',
            'status': 'error',
            'message': f"Error checking disk usage: {str(e)}"
        })

    # Check 5: Dead tuples ratio (table bloat)
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT relname, 
                       n_dead_tup::float / nullif(n_live_tup, 0) as dead_ratio
                FROM pg_stat_user_tables
                WHERE n_live_tup > 1000
                ORDER BY dead_ratio DESC
                LIMIT 5
            """)
            bloated_tables = []
            for row in cursor.fetchall():
                if row[1] and row[1] > 0.2:  # >20% dead tuples
                    bloated_tables.append({
                        'table': row[0],
                        'dead_ratio': row[1]
                    })

            if bloated_tables:
                results['status'] = 'warning'
                results['issues'].append(
                    f"{len(bloated_tables)} tables have high dead tuple ratios")
                results['checks'].append({
                    'name': 'table_bloat',
                    'status': 'warning',
                    'message': f"{len(bloated_tables)} tables need vacuum",
                    'tables': bloated_tables
                })
            else:
                results['checks'].append({
                    'name': 'table_bloat',
                    'status': 'passed',
                    'message': "No significant table bloat detected"
                })
    except Exception as e:
        results['checks'].append({
            'name': 'table_bloat',
            'status': 'error',
            'message': f"Error checking table bloat: {str(e)}"
        })

    # Check 6: Index usage
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT relname, 
                       idx_scan::float / nullif(seq_scan, 0) as index_usage_ratio
                FROM pg_stat_user_tables
                WHERE seq_scan > 100
                ORDER BY index_usage_ratio ASC
                LIMIT 5
            """)
            low_index_tables = []
            for row in cursor.fetchall():
                if row[1] is None or row[1] < 1.0:  # More sequential scans than index scans
                    low_index_tables.append({
                        'table': row[0],
                        'index_usage_ratio': row[1]
                    })

            if low_index_tables:
                results['status'] = 'warning'
                results['issues'].append(
                    f"{len(low_index_tables)} tables have low index usage")
                results['checks'].append({
                    'name': 'index_usage',
                    'status': 'warning',
                    'message': f"{len(low_index_tables)} tables may need better indexes",
                    'tables': low_index_tables
                })
            else:
                results['checks'].append({
                    'name': 'index_usage',
                    'status': 'passed',
                    'message': "Indexes are being used efficiently"
                })
    except Exception as e:
        results['checks'].append({
            'name': 'index_usage',
            'status': 'error',
            'message': f"Error checking index usage: {str(e)}"
        })

    # Output report
    output_file = f'../monitoring/health_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    os.makedirs('../monitoring', exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Health check results written to {output_file}")
    print(f"Status: {results['status'].upper()}")

    if results['issues']:
        print("\nIssues detected:")
        for issue in results['issues']:
            print(f"- {issue}")

    # Send email if requested and there are issues
    if send_email and email_recipient and results['status'] != 'healthy':
        send_email_alert(results, email_recipient)

    return results


def send_email_alert(results, recipient):
    """Send email alert about database issues."""
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"[{results['status'].upper()}] Database Health Alert - Educational Platform"
        msg['From'] = "eduplatform-monitor@example.com"
        msg['To'] = recipient

        body = f"""
        <html>
        <body>
            <h2>Database Health Alert</h2>
            <p><strong>Status:</strong> {results['status'].upper()}</p>
            <p><strong>Time:</strong> {results['timestamp']}</p>
            
            <h3>Issues:</h3>
            <ul>
                {''.join([f'<li>{issue}</li>' for issue in results['issues']])}
            </ul>
            
            <h3>Check Details:</h3>
            <table border="1" cellpadding="5">
                <tr>
                    <th>Check</th>
                    <th>Status</th>
                    <th>Message</th>
                </tr>
                {''.join([f'<tr><td>{check["name"]}</td><td>{check["status"]}</td><td>{check["message"]}</td></tr>' for check in results['checks']])}
            </table>
            
            <p>Please check the database monitoring dashboard for more details.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # Send email (configure your SMTP server details)
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.example.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_username = os.environ.get('SMTP_USERNAME', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.close()

        print(f"Alert email sent to {recipient}")
    except Exception as e:
        print(f"Failed to send email alert: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Database Health Check')
    parser.add_argument('--email', action='store_true',
                        help='Send email if issues found')
    parser.add_argument('--recipient', type=str, help='Email recipient')
    args = parser.parse_args()

    run_health_check(args.email, args.recipient)
