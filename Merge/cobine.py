import cv2
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw
import sqlite3
import io
import time
import qrcode
import threading
from Cryptodome.Cipher import AES
import base64
import os

# Object Detection Setup
classNames = []
classFile = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/coco.names"
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

configPath = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/frozen_inference_graph.pb"

net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

def getObjects(img, thres, nms, draw=True, objects=[]):
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    objectInfo = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in objects:
                objectInfo.append([box, className])
                if draw:
                    cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                    cv2.putText(img, classNames[classId - 1].upper(), (box[0] + 10, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(img, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
    return img, objectInfo

# Shopping Cart App with Object Detection Integratiaon
class ShoppingCartApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SMAPCA - Shopping Cart")
        self.root.geometry("800x480")  # Adjusted for Raspberry Pi screen
        self.root.grid_rowconfigure(0, weight=1)  # Make rows flexible
        self.root.grid_columnconfigure(0, weight=1)  # Make columns flexible
        self.root.configure(bg='#F0F0F0')

        # Create a canvas widget for scrollable content
        self.canvas = tk.Canvas(self.root, bg='#F0F0F0')
        self.canvas.grid(row=0, column=0, sticky="nsew")  # Use grid instead of pack

        # Create a scrollbar for the canvas
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")  # Use grid instead of pack

        # Configure canvas to work with scrollbar
        self.canvas.config(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", lambda e: self.canvas.config(scrollregion=self.canvas.bbox("all")))

        # Create a frame for all content inside the canvas
        self.content_frame = tk.Frame(self.canvas, bg='#F0F0F0')
        self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        # Ensure the content frame expands to fill the canvas
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Database connection and other initializations...
        self.conn = sqlite3.connect('barcode.db')
        self.cursor = self.conn.cursor()

        self.items = []
        self.quantities = []
        self.item_frames = {}
        self.last_scan_time = 0
        self.barcode_buffer = ""
        self.scanned_product = None
        self.scanned_product_data = None
        self.timer_started = False
        self.removal_mode = False

        # Header Frame
        self.header_frame = tk.Frame(self.content_frame, bg='white', pady=10)
        self.header_frame.grid(row=0, column=0, sticky="ew")  # Use grid instead of pack

        # Logo on the left
        try:
            logo_image = Image.open("C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/barcode/Logo3.png")
            logo_image = logo_image.resize((150, 60), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            self.logo_label = tk.Label(self.header_frame, image=self.logo_photo, bg='white')
            self.logo_label.grid(row=0, column=0, padx=10, sticky="w")  # Use grid instead of pack
        except Exception as e:
            print(f"Error loading logo: {e}")
            self.logo_label = tk.Label(self.header_frame, text="SMAPCA", fg='black', bg='white', font=("Arial", 16, "bold"))
            self.logo_label.grid(row=0, column=0, padx=10, sticky="w")  # Use grid instead of pack

        # Spacer to push the camera to the middle
        self.left_spacer = tk.Frame(self.header_frame, bg='white', width=10)
        self.left_spacer.grid(row=0, column=1, sticky="ew")  # Use grid instead of pack

        # Camera Feed in the middle of the header
        self.camera_frame = tk.Frame(self.header_frame, bg='black', highlightbackground="black", highlightthickness=0.5)
        self.camera_frame.grid(row=0, column=2, padx=10, pady=5)  # Use grid instead of pack

        # Label to display the camera feed
        self.camera_label = tk.Label(self.camera_frame, bg='black')
        self.camera_label.grid(row=0, column=0, pady=5, padx=5)  # Use grid instead of pack

        # Spacer to push the date/time to the right
        self.right_spacer = tk.Frame(self.header_frame, bg='white', width=10)
        self.right_spacer.grid(row=0, column=3, sticky="ew")  # Use grid instead of pack

        # Date and Time on the right
        self.datetime_label = tk.Label(self.header_frame, fg='black', bg='white', font=("Arial", 10))
        self.datetime_label.grid(row=0, column=4, padx=10, sticky="e")  # Use grid instead of pack
        self.update_datetime()

        # Title
        self.title_label = tk.Label(self.content_frame, text="Shopping Cart", font=("Arial", 18, "bold"), bg='#F0F0F0', fg='#333333')
        self.title_label.grid(row=1, column=0, pady=20, sticky="ew")  # Use grid instead of pack

        # Cart Items Frame
        self.cart_frame = tk.Frame(self.content_frame, bg='#F0F0F0')
        self.cart_frame.grid(row=2, column=0, pady=10, sticky="nsew")  # Use grid instead of pack

        # Welcome message label
        self.welcome_label = tk.Label(self.cart_frame, text="Welcome to SMAPCA, start your smart journey", font=("Arial", 12), bg='#F0F0F0', fg='#555555')
        self.welcome_label.grid(row=0, column=0, pady=20, sticky="ew")  # Use grid instead of pack

        # Total Amount
        self.total_label = tk.Label(self.content_frame, text="Total Amount: Rs. 0.00", font=("Arial", 16, "bold"), bg='#F0F0F0', fg='#333333')
        self.total_label.grid(row=3, column=0, pady=10, sticky="ew")  # Use grid instead of pack

        # Pay Now Button, Cart Sign, and QR Code Frame
        self.pay_qr_frame = tk.Frame(self.content_frame, bg='#F0F0F0')
        self.pay_qr_frame.grid(row=4, column=0, pady=20, sticky="ew")  # Use grid instead of pack

        # Cart Sign (🛒)
        self.cart_sign_label = tk.Label(self.pay_qr_frame, text="🛒", font=("Arial", 24), bg='#F0F0F0', fg='#4A90E2')
        self.cart_sign_label.grid(row=0, column=0, padx=10, sticky="w")  # Use grid instead of pack

        # Pay Now Button
        self.pay_button = tk.Button(self.pay_qr_frame, text="Pay Now", font=("Arial", 12), bg="#4CAF50", fg="white", bd=0, padx=10, pady=5, command=self.process_payment)
        self.pay_button.grid(row=0, column=1, padx=10, sticky="e")  # Use grid instead of pack

        # Remove Item Button
        self.remove_button = tk.Button(self.pay_qr_frame, text="Remove Item", font=("Arial", 12), bg="red", fg="white", bd=0, padx=10, pady=5, command=self.enable_removal_mode)
        self.remove_button.grid(row=0, column=2, padx=10, sticky="e")  # Use grid instead of pack

        # Placeholder for QR code
        self.qr_label = tk.Label(self.pay_qr_frame, bg='#F0F0F0')
        self.qr_label.grid(row=0, column=3, padx=10, sticky="e")  # Use grid instead of pack

        # Barcode scanning setup
        self.root.bind("<Key>", self.on_key_press)

        # Start object detection in a separate thread
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            exit()
        self.cap.set(3, 160)  # Reduce camera width
        self.cap.set(4, 120)  # Reduce camera height

        # Start updating the camera feed in the main window
        self.update_camera_feed()

    # Rest of the methods remain unchanged...

    def update_datetime(self):
        self.datetime_label.config(text=datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
        self.root.after(1000, self.update_datetime)

    def on_key_press(self, event):
        current_time = time.time()
        if current_time - self.last_scan_time < 2:
            return

        if event.char:
            self.barcode_buffer += event.char

        if event.keysym == "Return":
            barcode = self.barcode_buffer.strip()
            self.barcode_buffer = ""
            self.last_scan_time = current_time

            if self.removal_mode:
                self.remove_item_from_cart(barcode)
            else:
                self.process_barcode(barcode)

    def process_barcode(self, barcode):
        if not barcode:
            return

        self.cursor.execute("SELECT Name, Price, Image, Description FROM Smapca WHERE barcode = ?", (barcode,))
        item = self.cursor.fetchone()

        if item:
            name, price, image_blob, desc = item
            self.scanned_product = name
            self.scanned_product_data = {"name": name, "price": price, "desc": desc, "image_blob": image_blob}
            self.timer_started = True
            self.start_timer()
        else:
            messagebox.showwarning("Not Found", "Item not found in the database.")

    def start_timer(self):
        if self.timer_started:
            self.root.after(5000, self.check_object_detection)

    def check_object_detection(self):
        if self.scanned_product:
            #messagebox.showinfo("Timeout", "Object not detected within 5 seconds.")
            self.scanned_product = None
            self.scanned_product_data = None
            self.timer_started = False

    def update_camera_feed(self):
        success, img = self.cap.read()
        if success:
            # Perform object detection
            result, objectInfo = getObjects(img, 0.45, 0.2, objects=[self.scanned_product] if self.scanned_product else [])

            # If the scanned product is detected, add it to the cart
            if self.scanned_product and objectInfo:
                for obj in objectInfo:
                    if obj[1] == self.scanned_product:
                        self.add_item_to_cart(
                            self.scanned_product_data["name"],
                            self.scanned_product_data["price"],
                            self.scanned_product_data["desc"],
                            self.scanned_product_data["image_blob"]
                        )
                        self.scanned_product = None
                        self.scanned_product_data = None
                        self.timer_started = False
                        break

            # Convert the image to RGB and resize it
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (120, 90))  # Resize camera feed to make it smaller
            img = Image.fromarray(img)
            img = ImageTk.PhotoImage(image=img)

            # Update the camera label with the new image
            self.camera_label.config(image=img)
            self.camera_label.image = img

        # Schedule the next update
        self.root.after(10, self.update_camera_feed)

    def add_item_to_cart(self, name, price, desc, image_blob):
        for i, item in enumerate(self.items):
            if item["name"] == name:
                self.quantities[i] += 1  # Increase the quantity automatically
                self.update_total()
                return  # Exit the function since the item already exists

        frame = tk.Frame(self.cart_frame, bg='white', pady=10, padx=10, highlightbackground="#E0E0E0", highlightthickness=1)
        frame.pack(pady=5, fill=tk.X, padx=20)

        try:
            image = Image.open(io.BytesIO(image_blob))
            image = image.resize((60, 60), Image.LANCZOS)
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

        name_label = tk.Label(text_frame, text=name, font=("Arial", 10, "bold"), bg='white', fg='#333333')
        name_label.pack(anchor='w')

        desc_label = tk.Label(text_frame, text=desc, font=("Arial", 9), bg='white', fg='#555555', wraplength=300, justify='left')
        desc_label.pack(anchor='w', pady=2)

        price_qty_frame = tk.Frame(frame, bg='white')
        price_qty_frame.pack(side=tk.LEFT, padx=20)

        price_label = tk.Label(price_qty_frame, text=f"Rs. {price:.2f}", font=("Arial", 10), bg='white', fg='#333333')
        price_label.pack(anchor='e', pady=2)

        qty_label = tk.Label(price_qty_frame, text="Qty: 1", font=("Arial", 10), bg='white', fg='#333333')
        qty_label.pack(anchor='e', pady=2)

        self.items.append({"name": name, "price": price, "desc": desc, "image": image_blob, "frame": frame, "qty_label": qty_label})
        self.quantities.append(1)  # Store quantity as an integer

        self.update_total()

    def remove_item_from_cart(self, barcode):
        """Decreases item quantity or removes it completely if the quantity is 1."""
        self.cursor.execute("SELECT Name FROM Smapca WHERE barcode = ?", (barcode,))
        item = self.cursor.fetchone()

        if not item:
            return  # No messagebox to avoid interrupting the process

        name = item[0]

        # Find the item in the cart
        for i, cart_item in enumerate(self.items):
            if cart_item["name"] == name:
                if self.quantities[i] > 1:
                    self.quantities[i] -= 1  # Reduce quantity by 1
                    cart_item["qty_label"].config(text=f"Qty: {self.quantities[i]}")  # Update UI label
                else:
                    cart_item["frame"].destroy()  # Remove UI element
                    del self.items[i]  # Remove item from list
                    del self.quantities[i]  # Remove quantity tracking

                self.update_total()  # Update total price
                return  # Exit function after successful removal




    def update_total(self):
        total = 0
        for i, item in enumerate(self.items):
            total += item["price"] * self.quantities[i]  # No .get(), use integer directly
            item["qty_label"].config(text=f"Qty: {self.quantities[i]}")  # Update quantity label

        self.total_label.config(text=f"Total Amount: Rs. {total:.2f}")

        if len(self.items) == 0:
            self.welcome_label.pack(pady=20)
        else:
            self.welcome_label.pack_forget()

    def enable_removal_mode(self):
        """Enables removal mode and shows a temporary notification."""
        self.removal_mode = True

        # Show a temporary notification (disappears after 2 seconds)
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)  # No title bar
        popup.geometry("300x50+500+400")  # Adjust position
        popup.configure(bg="red")

        label = tk.Label(popup, text="Scan item to remove", fg="white", bg="red", font=("Arial", 14, "bold"))
        label.pack(expand=True)

        # Close the popup after 2 seconds
        self.root.after(2000, popup.destroy)

        # Auto-disable removal mode after 10 seconds
        self.root.after(10000, self.disable_removal_mode)

    def disable_removal_mode(self):
        """Automatically exits removal mode after timeout."""
        self.removal_mode = False


    AES_KEY = b"treegodbedoofchi"  # Ensure this key is kept secret in the mobile app

    """def encrypt_data(self, data):
        cipher = AES.new(self.AES_KEY, AES.MODE_EAX)  # AES with EAX mode for security
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())

        # Encode both the nonce and ciphertext as Base64 to store in the QR code
        encrypted_qr_data = base64.b64encode(nonce + ciphertext).decode()
        return encrypted_qr_data"""
    def encrypt_data(self,data):
        cipher = AES.new(self.AES_KEY, AES.MODE_GCM)  # Using AES-GCM mode
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())

        # Concatenate nonce + tag + ciphertext and encode as Base64
        encrypted_qr_data = base64.b64encode(nonce + tag + ciphertext).decode()
        return encrypted_qr_data


    def process_payment(self):
        if not self.items:
            messagebox.showinfo("Empty Cart", "Your cart is empty. Add items to proceed.")
            return

        # Convert cart details to string
        cart_data = "Cart Details:\n"
        for item, qty in zip(self.items, self.quantities):
            cart_data += f"{item['name']} - Rs. {item['price']:.2f}\nQuantity- {qty}\n"
        cart_data += f"Total: Rs. {sum(item['price'] * qty for item, qty in zip(self.items, self.quantities)):.2f}\n"

        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        cart_data += f"Date & Time:{timestamp}"

        # Encrypt the cart data
        encrypted_cart_data = self.encrypt_data(cart_data)  # Use self.encrypt_data()

        # Generate QR code with encrypted data
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=2,
        )
        qr.add_data(encrypted_cart_data)
        qr.make(fit=True)

        # Convert QR to an image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((80, 80), Image.LANCZOS)

        # Display the QR code
        qr_img_tk = ImageTk.PhotoImage(qr_img)
        self.qr_label.config(image=qr_img_tk)
        self.qr_label.image = qr_img_tk

if __name__ == "__main__":
    root = tk.Tk()
    app = ShoppingCartApp(root)
    root.mainloop()