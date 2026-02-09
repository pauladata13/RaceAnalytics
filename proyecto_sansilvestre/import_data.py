import json
import time
import mysql.connector
from mysql.connector import Error

# Configuration
JSON_FILE='proyecto_sansilvestre/carreras_san_silvestre.json'
DB_CONFIG={
    'host':'localhost',
    'user':'root',
    'password':'root',
    'database':'sansilvestre_db'
}

def create_tables(cursor):
    # 'runners' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS runners (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        gender ENUM('M', 'F'),
        UNIQUE(name)
    );
    """)

    # 'races' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS races (
        id INT AUTO_INCREMENT PRIMARY KEY,
        location VARCHAR(255) NOT NULL,
        year INT NOT NULL,
        distance VARCHAR(100),
        UNIQUE(location, year)
    );
    """)

    # 'results' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS race_results (
        id INT AUTO_INCREMENT PRIMARY KEY,
        runner_id INT NOT NULL,
        race_id INT NOT NULL,
        finish_time TIME,
        age_group VARCHAR(6),
        FOREIGN KEY (runner_id) REFERENCES runners(id) ON DELETE CASCADE,
        FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE
    );
    """)

def connect_to_db():
    retries=5
    while retries>0:
        try:
            connection=mysql.connector.connect(**DB_CONFIG)
            return connection
        except Error:
            print(f"Trying to connect to MySQL database...\nAttempts remaining: {retries}")
            time.sleep(3)
            retries-=1
    return None

def import_data():
    conn = connect_to_db()
    if not conn:
        print("❌ Connection to MySQL/Docker failed.")
        return

    try:
        cursor = conn.cursor()
        
        # Create structure
        create_tables(cursor)

        # Load .json file
        with open(JSON_FILE, 'r', encoding='utf-8') as f: data = json.load(f)

        print(f"Processing {len(data)} entries, please wait...")

        # Insert data
        for item in data:
            # Insert race
            cursor.execute("SELECT id FROM races WHERE location = %s AND year = %s", 
                           (item['location'], item['race_date']))
            race = cursor.fetchone()
            if race:
                race_id = race[0]
            else:
                cursor.execute("INSERT INTO races (location, year, distance) VALUES (%s, %s, %s)", 
                               (item['location'], item['race_date'], item['race_distance']))
                race_id = cursor.lastrowid

            # Insert runner
            cursor.execute("SELECT id FROM runners WHERE name = %s", (item['runner_name'],))
            runner = cursor.fetchone()
            if runner:
                runner_id = runner[0]
            else:
                cursor.execute("INSERT INTO runners (name, gender) VALUES (%s, %s)", 
                               (item['runner_name'], item['gender']))
                runner_id = cursor.lastrowid

            # Insert result
            # Check for duplicate entry
            cursor.execute("SELECT id FROM race_results WHERE runner_id = %s AND race_id = %s", (runner_id, race_id))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO race_results (runner_id, race_id, finish_time, age_group)
                    VALUES (%s, %s, %s, %s)
                """, (runner_id, race_id, item['finish_time'], item['age_group']))

        conn.commit()
        print(f"\(^-^)/ Done!\nAll data was imported to '{DB_CONFIG['database']}' successfully\n\nSTEPS TO ENTER IN THE DATABASE\n1. Execute the following command in a terminal:\n-  docker exec -it carrera_mysql mysql -u root -p\n2. Enter the following MySQL database password:\n-  {DB_CONFIG['password']}\n3. Enter in the database:\n- USE sansilvestre_db;\n\nAnd now you're in! We hope\nthat everything went ok :)")

    except Error as e:
        print(f"❌ SQL error: {e}")
    except FileNotFoundError:
        print(f"❌ '{JSON_FILE}' does not exist or is a directory.")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    import_data()