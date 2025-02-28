import pymongo
import base64

if __name__ == '__main__':
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    print('connected!')

    # Connect to database and collection
    db = client['smapca']
    collection = db['object']

    # Read and encode images
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    # Insert data with images
    insert = [
        #{'name': 'Bottle', 'price': 99, 'des': 'hsakfbjhccbjkaksavj', 'image': encode_image('dataset/images/download (1).jpeg')},
        #{'name': 'Bag', 'price': 489, 'des': 'hsakfbjhccbjkaksavj', 'image': encode_image('dataset/images/download (2).jpeg')},
        #{'name': 'Mouse', 'price': 599, 'des': 'hsakfbjhccbjkaksavj', 'image': encode_image('dataset/images/download.jpeg')},
        {'name': 'cell phone', 'price': 899, 'des': 'hsakfbjhccbjkaksavj', 'image': encode_image('dataset/images/images (1).jpeg')},
    ]

    collection.insert_many(insert)
