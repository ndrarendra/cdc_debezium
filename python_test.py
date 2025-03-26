import mysql.connector
import time

def test_crud_operations():
    # Connect to MySQL (adjust host/port if needed; here we assume the MySQL container is exposed on port 3307)
    conn = mysql.connector.connect(
        host="localhost",
        port=3307,
        user="demo",
        password="demo",
        database="demo_db"
    )
    cursor = conn.cursor()

    # ---- INSERT Operation ----
    print("Performing INSERT operation...")
    cursor.execute("INSERT INTO users (id, name, email) VALUES (18, 'Alice', 'alice@example.com');")
    conn.commit()
    print("Inserted row with ID 13.")
    time.sleep(3)  # Wait a few seconds to allow Debezium to capture the change

    # ---- UPDATE Operation ----
    print("Performing UPDATE operation...")
    cursor.execute("UPDATE users SET name='Alice Updated', email='alice_updated@example.com' WHERE id=18;")
    conn.commit()
    print("Updated row with ID 13.")
    time.sleep(3)

    # ---- DELETE Operation ----
    print("Performing DELETE operation...")
    cursor.execute("DELETE FROM users WHERE id=17;")
    conn.commit()
    print("Deleted row with ID 15.")
    time.sleep(3)

    cursor.close()
    conn.close()
    print("CRUD operations complete.")

if __name__ == "__main__":
    test_crud_operations()
