import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox
import time  # Import time module for cooldown

# Connect to the database
connection = sqlite3.connect('barcode.db')
cursor = connection.cursor()

# Create the table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Smapca (
        Barcode TEXT UNIQUE,
        Name TEXT,
        Image BLOB,
        Price REAL,
        Description TEXT
    )
''')

# Cooldown variable to prevent rapid duplicate inserts
last_insert_time = 0  

# Function to insert product
def insert_product():
    global last_insert_time  # Use global variable for cooldown
    barcode = barcode_entry.get().strip()
    name = name_entry.get().strip()
    price = price_entry.get().strip()
    description = description_entry.get().strip()
    image_path = image_path_label.cget("text")

    if not barcode or not name or not price or not description or image_path == "No file selected":
        messagebox.showerror("Input Error", "All fields are required!")
        return

    # 🔹 Cooldown logic: Prevent multiple fast inserts (Set 1-second cooldown)
    current_time = time.time()
    if current_time - last_insert_time < 1:  
        return  # Ignore input if less than 1 second has passed

    last_insert_time = current_time  # Update the last insert timestamp

    try:
        price = float(price)  
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()

        cursor.execute('''
            INSERT INTO Smapca (Barcode, Name, Image, Price, Description)
            VALUES (?, ?, ?, ?, ?)
        ''', (barcode, name, image_data, price, description))

        connection.commit()
        messagebox.showinfo("Success", f"Product '{name}' added successfully!")
        clear_inputs()

    except ValueError:
        messagebox.showerror("Input Error", "Invalid price! Enter a valid number.")
    except FileNotFoundError:
        messagebox.showerror("File Error", "Image file not found!")

# Function to search product by Barcode
def search_product():
    barcode = barcode_entry.get().strip()
    if not barcode:
        messagebox.showerror("Search Error", "Please enter a barcode to search!")
        return

    cursor.execute("SELECT Name, Price, Description FROM Smapca WHERE Barcode=?", (barcode,))
    result = cursor.fetchone()

    if result:
        name_entry.delete(0, tk.END)
        name_entry.insert(0, result[0])

        price_entry.delete(0, tk.END)
        price_entry.insert(0, str(result[1]))

        description_entry.delete(0, tk.END)
        description_entry.insert(0, result[2])

        messagebox.showinfo("Search Result", f"Product Found: {result[0]}")
    else:
        messagebox.showerror("Not Found", "No product found with this barcode!")

# Function to update product details
def update_product():
    barcode = barcode_entry.get().strip()
    name = name_entry.get().strip()
    price = price_entry.get().strip()
    description = description_entry.get().strip()
    
    if not barcode:
        messagebox.showerror("Update Error", "Enter a barcode to update!")
        return

    try:
        price = float(price)  
        cursor.execute('''
            UPDATE Smapca 
            SET Name=?, Price=?, Description=? 
            WHERE Barcode=?
        ''', (name, price, description, barcode))

        if cursor.rowcount:
            connection.commit()
            messagebox.showinfo("Update Success", f"Product '{name}' updated successfully!")
        else:
            messagebox.showerror("Update Error", "Barcode not found!")

    except ValueError:
        messagebox.showerror("Input Error", "Invalid price!")

# Function to delete a product by barcode
def delete_product():
    barcode = barcode_entry.get().strip()
    if not barcode:
        messagebox.showerror("Delete Error", "Enter a barcode to delete!")
        return

    cursor.execute("DELETE FROM Smapca WHERE Barcode=?", (barcode,))
    if cursor.rowcount:
        connection.commit()
        clear_inputs()
        messagebox.showinfo("Delete Success", "Product deleted successfully!")
    else:
        messagebox.showerror("Delete Error", "Barcode not found!")

# Function to browse for an image
def browse_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
    if file_path:
        image_path_label.config(text=file_path)

# Function to clear input fields
def clear_inputs():
    barcode_entry.delete(0, tk.END)
    name_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    description_entry.delete(0, tk.END)
    image_path_label.config(text="No file selected")

# Create GUI window
root = tk.Tk()
root.title("Product Management System")

# Labels and entry fields
tk.Label(root, text="Barcode:").grid(row=0, column=0, padx=10, pady=5)
barcode_entry = tk.Entry(root)
barcode_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Name:").grid(row=1, column=0, padx=10, pady=5)
name_entry = tk.Entry(root)
name_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Price:").grid(row=2, column=0, padx=10, pady=5)
price_entry = tk.Entry(root)
price_entry.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Description:").grid(row=3, column=0, padx=10, pady=5)
description_entry = tk.Entry(root)
description_entry.grid(row=3, column=1, padx=10, pady=5)

# File selection button
tk.Button(root, text="Select Image", command=browse_image).grid(row=4, column=0, padx=10, pady=5)
image_path_label = tk.Label(root, text="No file selected", fg="gray")
image_path_label.grid(row=4, column=1, padx=10, pady=5)

# CRUD Buttons
tk.Button(root, text="Add Product", command=insert_product).grid(row=5, column=0, pady=10)
tk.Button(root, text="Search Product", command=search_product).grid(row=5, column=1, pady=10)

tk.Button(root, text="Update Product", command=update_product).grid(row=6, column=0, pady=10)
tk.Button(root, text="Delete Product", command=delete_product).grid(row=6, column=1, pady=10)

# Run the GUI
root.mainloop()

# Close the database connection when done
connection.close()
