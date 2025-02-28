import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw
import sqlite3
import io
import time
import qrcode  # For generating QR codes

class ShoppingCartApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SMAPCA - Shopping Cart")
        self.root.geometry("800x900")
        self.root.configure(bg='#F0F0F0')  # Light gray background
        
        # Database connection
        self.conn = sqlite3.connect('barcode.db')  # Connect to your existing database
        self.cursor = self.conn.cursor()
        
        self.items = []  # List to store cart items
        self.quantities = []  # List to store quantities
        self.item_frames = {}  # Dictionary to store item frames for easy removal
        self.last_scan_time = 0  # Store timestamp of last scan
        
        # Header
        self.header_frame = tk.Frame(self.root, bg='white', pady=10)  # Blue header
        self.header_frame.pack(fill=tk.X)

        # Load and display the logo
        try:
            logo_image = Image.open("C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/barcode/Logo3.png")  # Replace with your actual image path
            logo_image = logo_image.resize((200, 80), Image.LANCZOS)  # Resize if needed
            self.logo_photo = ImageTk.PhotoImage(logo_image)  # Convert image
            self.logo_label = tk.Label(self.header_frame, image=self.logo_photo, bg='white')
            self.logo_label.pack(side=tk.LEFT, padx=40)
        except Exception as e:
            print(f"Error loading logo: {e}")
            self.logo_label = tk.Label(self.header_frame, text="SMAPCA", fg='black', bg='white', font=("Arial", 16, "bold"))
            self.logo_label.pack(side=tk.LEFT, padx=10)

        # Date and Time
        self.datetime_label = tk.Label(self.header_frame, fg='black', bg='white', font=("Arial", 16))
        self.datetime_label.pack(side=tk.RIGHT, padx=10)
        self.update_datetime()
        
        # Title
        self.title_label = tk.Label(self.root, text="Shopping Cart", font=("Arial", 24, "bold"), bg='#F0F0F0', fg='#333333')
        self.title_label.pack(pady=20)
        
        # Cart Items Frame
        self.cart_frame = tk.Frame(self.root, bg='#F0F0F0')
        self.cart_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Welcome message label
        self.welcome_label = tk.Label(self.cart_frame, text="Welcome to SMAPCA, start your smart journey", font=("Arial", 14), bg='#F0F0F0', fg='#555555')
        self.welcome_label.pack(pady=20)
        
        # Total Amount
        self.total_label = tk.Label(self.root, text="Total Amount: Rs. 0.00", font=("Arial", 16, "bold"), bg='#F0F0F0', fg='#333333')
        self.total_label.pack(pady=10)
        
        # Pay Now Button, Cart Sign, and QR Code Frame
        self.pay_qr_frame = tk.Frame(self.root, bg='#F0F0F0')
        self.pay_qr_frame.pack(pady=20)
        
        # Cart Sign (🛒)
        self.cart_sign_label = tk.Label(self.pay_qr_frame, text="🛒", font=("Arial", 24), bg='#F0F0F0', fg='#4A90E2')
        self.cart_sign_label.pack(side=tk.LEFT, padx=10)
        
        # Pay Now Button
        self.pay_button = tk.Button(self.pay_qr_frame, text="Pay Now", font=("Arial", 14), bg="#4CAF50", fg="white", bd=0, padx=20, pady=10, command=self.process_payment)
        self.pay_button.pack(side=tk.LEFT, padx=10)
        
        # Placeholder for QR code
        self.qr_label = tk.Label(self.pay_qr_frame, bg='#F0F0F0')
        self.qr_label.pack(side=tk.LEFT, padx=10)
        
        # Barcode scanning setup
        self.barcode_buffer = ""  # Buffer to store barcode input
        self.root.bind("<Key>", self.on_key_press)  # Capture all key presses
        
        self.update_total()
    
    def update_datetime(self):
        """Update the date and time in the header."""
        self.datetime_label.config(text=datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
        self.root.after(1000, self.update_datetime)
    
    def on_key_press(self, event):
        """Capture key presses for barcode scanning with a delay interval."""
        current_time = time.time()
        if current_time - self.last_scan_time < 2:
            return  # Ignore input if it's within 2 seconds of the last scan
        
        if event.char:  # Check if the key press has a character
            self.barcode_buffer += event.char  # Append the character to the buffer
        
        # Check if the Enter key is pressed (barcode scanner sends Enter after the barcode)
        if event.keysym == "Return":
            self.process_barcode(self.barcode_buffer.strip())  # Process the barcode
            self.barcode_buffer = ""  # Clear the buffer for the next scan
            self.last_scan_time = current_time  # Update last scan time
    
    def process_barcode(self, barcode):
        """Process the scanned barcode."""
        if not barcode:
            return  # Ignore empty barcodes
        
        # Query the database
        self.cursor.execute("SELECT Name, Price, Image, Description FROM Smapca WHERE barcode = ?", (barcode,))
        item = self.cursor.fetchone()
        
        if item:
            name, price, image_blob, desc = item
            self.add_item_to_cart(name, price, desc, image_blob)
        else:
            messagebox.showwarning("Not Found", "Item not found in the database.")
    
    def add_item_to_cart(self, name, price, desc, image_blob):
        """Add an item to the shopping cart and update the UI."""
        for i, item in enumerate(self.items):
            if item["name"] == name:
                self.quantities[i].set(self.quantities[i].get() + 1)
                self.update_total()
                return
        
        frame = tk.Frame(self.cart_frame, bg='white', pady=10, padx=10, highlightbackground="#E0E0E0", highlightthickness=1)
        frame.pack(pady=5, fill=tk.X, padx=20)
        
        try:
            image = Image.open(io.BytesIO(image_blob))  
            image = image.resize((80, 80), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            img_label = tk.Label(frame, image=photo, bg='white')
            img_label.image = photo  
            img_label.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            print(f"Error loading image: {e}")
            img_label = tk.Label(frame, text="No Image", bg='white')
            img_label.pack(side=tk.LEFT, padx=10)
        
        text_frame = tk.Frame(frame, bg='white')
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        name_label = tk.Label(text_frame, text=name, font=("Arial", 12, "bold"), bg='white', fg='#333333')
        name_label.pack(anchor='w')
        
        desc_label = tk.Label(text_frame, text=desc, font=("Arial", 10), bg='white', fg='#555555', wraplength=300, justify='left')
        desc_label.pack(anchor='w', pady=2)
        
        price_qty_frame = tk.Frame(frame, bg='white')
        price_qty_frame.pack(side=tk.LEFT, padx=20)
        
        price_label = tk.Label(price_qty_frame, text=f"Rs. {price:.2f}", font=("Arial", 12), bg='white', fg='#333333')
        price_label.pack(anchor='e', pady=2)
        
        qty_var = tk.IntVar(value=1)
        self.quantities.append(qty_var)
        qty_entry = tk.Spinbox(price_qty_frame, from_=1, to=99, textvariable=qty_var, width=5, command=self.update_total)
        qty_entry.pack(anchor='e', pady=2)
        
        remove_button = tk.Button(frame, text="X", font=("Arial", 10), bg="#FF5252", fg="white", bd=0, command=lambda f=frame: self.remove_item(f))
        remove_button.pack(side=tk.RIGHT, padx=10)
        
        self.items.append({"name": name, "price": price, "desc": desc, "image": image_blob, "frame": frame})
        self.update_total()

    def remove_item(self, frame):
        """Remove an item from the cart."""
        for i, item in enumerate(self.items):
            if item["frame"] == frame:
                # Remove the item from the list
                self.items.pop(i)
                self.quantities.pop(i)
                frame.destroy()  # Remove the frame from the UI
                self.update_total()
                break
    
    def update_total(self):
        total = sum(item["price"] * qty.get() for item, qty in zip(self.items, self.quantities))
        self.total_label.config(text=f"Total Amount: Rs. {total:.2f}")
        
        # Show or hide the welcome message based on whether the cart is empty
        if len(self.items) == 0:
            self.welcome_label.pack(pady=20)
        else:
            self.welcome_label.pack_forget()
    
    def process_payment(self):
        """Generate a QR code with cart data and display it beside the Pay Now button."""
        if not self.items:
            messagebox.showinfo("Empty Cart", "Your cart is empty. Add items to proceed.")
            return
        
        # Prepare the cart data as a string
        cart_data = "Cart Details:\n"
        for item, qty in zip(self.items, self.quantities):
            cart_data += f"{item['name']} - Rs. {item['price']:.2f} x {qty.get()}\n"
        cart_data += f"Total: Rs. {sum(item['price'] * qty.get() for item, qty in zip(self.items, self.quantities)):.2f}"
        
        # Generate the QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,  # Smaller box size for a smaller QR code
            border=2,    # Smaller border
        )
        qr.add_data(cart_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize the QR code to make it smaller
        qr_img = qr_img.resize((100, 100), Image.LANCZOS)
        
        # Convert the QR code image to a format Tkinter can display
        qr_img_tk = ImageTk.PhotoImage(qr_img)
        self.qr_label.config(image=qr_img_tk)
        self.qr_label.image = qr_img_tk  # Keep a reference to avoid garbage collection

if __name__ == "__main__":
    root = tk.Tk()
    app = ShoppingCartApp(root)
    root.mainloop()