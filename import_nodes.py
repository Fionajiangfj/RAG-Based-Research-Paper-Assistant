import os
import sys
import logging
import argparse
import psycopg2
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def import_nodes_psql(sql_file_path, database_url):
    """Import nodes from SQL file using psql command-line tool"""
    try:
        logger.info(f"Importing {sql_file_path} to {database_url}")
        
        # Use subprocess to call psql
        result = subprocess.run(
            ['psql', database_url, '-f', sql_file_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Error running psql: {result.stderr}")
            return False
        
        logger.info(f"psql output: {result.stdout}")
        logger.info("Successfully imported nodes into database")
        return True
    except Exception as e:
        logger.error(f"Error importing nodes: {str(e)}")
        return False

def import_nodes_psycopg2(sql_file_path, database_url):
    """Import nodes from SQL file using psycopg2"""
    try:
        # Connect to the database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        logger.info(f"Connected to database")
        
        # Read SQL file
        with open(sql_file_path, 'r') as f:
            sql_script = f.read()
            logger.info(f"Read SQL file: {sql_file_path} ({len(sql_script)} bytes)")
        
        # Execute SQL script
        with conn.cursor() as cursor:
            cursor.execute(sql_script)
            logger.info("Successfully executed SQL script")
        
        # Verify import
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM nodes;")
            count = cursor.fetchone()[0]
            logger.info(f"Database contains {count} nodes")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error importing nodes with psycopg2: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import nodes from SQL file to database')
    parser.add_argument('--file', type=str, required=True, help='Path to SQL file')
    parser.add_argument('--db-url', type=str, help='Database URL (or use DATABASE_URL env var)')
    parser.add_argument('--method', type=str, choices=['psql', 'psycopg2'], default='psycopg2',
                        help='Method to use for importing (default: psycopg2)')
    
    args = parser.parse_args()
    
    # Get database URL from args or environment
    database_url = args.db_url or os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("Database URL not provided. Use --db-url or set DATABASE_URL env var")
        sys.exit(1)
    
    # Import nodes using the specified method
    if args.method == 'psql':
        success = import_nodes_psql(args.file, database_url)
    else:
        success = import_nodes_psycopg2(args.file, database_url)
    
    sys.exit(0 if success else 1) 