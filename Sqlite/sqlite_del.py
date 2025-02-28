import sqlite3

# Step 1: Connect to the SQLite database
connection = sqlite3.connect('example.db')

# Step 2: Create a cursor object to interact with the database
cursor = connection.cursor()

# Step 3: Define the name of the record to delete
name_to_delete = 'cell phone'

# Step 4: Execute the DELETE command
cursor.execute('''
    DELETE FROM Smapca WHERE Name = ?
''', (name_to_delete,))

# Step 5: Commit the changes to the database
connection.commit()

# Step 6: Check if any rows were deleted
if cursor.rowcount > 0:
    print(f"Record with name '{name_to_delete}' deleted successfully!")
else:
    print(f"No record found with name '{name_to_delete}'.")

# Step 7: Close the connection
connection.close()
