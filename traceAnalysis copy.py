from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pandas as pd
from decimal import Decimal
import time
import os

class TransactionHandler(FileSystemEventHandler):
    def __init__(self, file_path):
        self.file_path = file_path
        self.wallet = []
        self.last_processed_row = 0
        self.process_existing_data()  # Process existing data at startup

    def process_existing_data(self):
        if os.path.exists(self.file_path):
            self.process_transactions(pd.read_csv(self.file_path))
            print("Processed existing data.")

    def on_modified(self, event):
        print(f"File modified: {event.src_path}")
        if event.src_path == self.file_path:
            self.process_new_transactions()

    def process_new_transactions(self):
        df = pd.read_csv(self.file_path)
        new_transactions = df.iloc[self.last_processed_row:]
        if not new_transactions.empty:
            self.process_transactions(new_transactions)
            self.last_processed_row = len(df)
            print("Processed new transactions.")

    def process_transactions(self, transactions):
        for _, transaction in transactions.iterrows():
            quantity = Decimal(transaction['Quantity'])
            price = Decimal(transaction['Price'])
            side = transaction['Side']

            if side == 'buy':
                self.wallet.append({'quantity': quantity, 'price': price})
            elif side == 'sell':
                self.process_sale(quantity, price)

    def process_sale(self, sell_quantity, sell_price):
        for buy in list(self.wallet):
            if sell_quantity <= 0:
                break
            if buy['quantity'] <= sell_quantity:
                sell_quantity -= buy['quantity']
                print(f"Sold {buy['quantity']} from buy at ${buy['price']} at ${sell_price}")
                self.wallet.remove(buy)
            else:
                buy['quantity'] -= sell_quantity
                print(f"Sold {sell_quantity} from buy at ${buy['price']} at ${sell_price}")
                sell_quantity = 0

if __name__ == "__main__":
    path = 'D:/VVWoodworks Market Trader/AI-Bot-Trader/trace.csv'
    event_handler = TransactionHandler(path)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(path), recursive=False)
    observer.start()
    print("Observer started, watching for file changes.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
