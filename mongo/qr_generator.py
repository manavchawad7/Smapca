import qrcode
import os
import json

class QRGenerator:
    def __init__(self, qr_dir="static"):
        self.qr_dir = qr_dir
        if not os.path.exists(self.qr_dir):
            os.makedirs(self.qr_dir)

    def generate_qr(self, data):
        """
        Generate a QR code with JSON data.
        :param data: List of dictionaries containing item details.
        :return: Path to the generated QR code image.
        """
        # Convert the data to a JSON string
        qr_data = json.dumps(data, indent=2)
        
        # Generate the QR code
        qr = qrcode.make(qr_data)
        
        # Save the QR code image
        qr_path = os.path.join(self.qr_dir, "qr_code.png")
        qr.save(qr_path)
        
        return qr_path