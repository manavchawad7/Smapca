import sqlite3

class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    def find_one(self, query):
        """Finds one record from the SQLite database matching the query."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # To return results as dictionaries
        cursor = conn.cursor()
        
        # Assuming 'name' is the key to search for
        name = query.get("name")
        cursor.execute("SELECT * FROM Smapca WHERE Name = ?", (name,))
        result = cursor.fetchone()
        
        conn.close()
        
        return dict(result) if result else None
