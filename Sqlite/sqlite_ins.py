import sqlite3

# Step 1: Connect to the SQLite database (or create it if it doesn't exist)
connection = sqlite3.connect('example.db')

# Step 2: Create a cursor object to interact with the database
cursor = connection.cursor()

# Step 3: Create the Smapca table (if not already created)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Smapca (
        Name TEXT,
        Image BLOB,   -- Using BLOB for storing image data (can also use TEXT for image URLs)
        Price REAL,
        Description TEXT
    )
''')

# Step 4: Insert data into the Smapca table
# Example 1: Insert a record
#cursor.execute('''
#    INSERT INTO Smapca (Name, Image, Price, Description)
#    VALUES (?, ?, ?, ?)
#''', ('Product1', None, 29.99, 'Description of Product1'))

# Example 2: Inserting an image file (as BLOB) into the database
# Open the image file in binary mode and insert it as a BLOB.
with open('C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Sqlite/bag.jpg', 'rb') as image_file:
    image_data = image_file.read()
    cursor.execute('''
        INSERT INTO Smapca (Name, Image, Price, Description)
        VALUES (?, ?, ?, ?)
    ''', ('backpack', image_data, 699.59, 'Description of Product'))

# Alternatively, inserting multiple records at once
#data = [
#    ('cell phone',"Phone.jpeg" , 1999.99, 'Description of Product3'),
#    ('Bag', None, 39.99, 'Description of Product4')
#]
#cursor.executemany('''
#    INSERT INTO Smapca (Name, Image, Price, Description)
#    VALUES (?, ?, ?, ?)
#''', data)

# Step 5: Commit the changes
connection.commit()

# Step 6: Close the connection
connection.close()

print("Data inserted successfully!")
