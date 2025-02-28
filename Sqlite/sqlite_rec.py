import sqlite3
from PIL import Image
import io

# Step 1: Connect to the SQLite database
connection = sqlite3.connect('example.db')

# Step 2: Create a cursor object to interact with the database
cursor = connection.cursor()

# Step 3: Fetch data from the Smapca table
cursor.execute('SELECT Name, Image, Price, Description FROM Smapca')

# Step 4: Retrieve the results
rows = cursor.fetchall()

# Step 5: Loop through the rows and display data
for row in rows:
    name, image_data, price, description = row
    print(f"Name: {name}")
    print(f"Price: {price}")
    print(f"Description: {description}")
    
    # If image data exists (i.e., not None), display it
    if image_data:
        try:
            # Convert the image data (BLOB) into an image
            image = Image.open(io.BytesIO(image_data))  # Convert BLOB to image
            image.show()  # This will open the image using the default image viewer
        except Exception as e:
            print(f"Error displaying image for {name}: {e}")
    else:
        print("No image available")

# Step 6: Close the connection
connection.close()
