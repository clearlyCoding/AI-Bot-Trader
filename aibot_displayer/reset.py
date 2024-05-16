import os
import django
import csv
CSV_PATH  = "D:/VVWoodworks Market Trader/AI-Bot-Trader/trace.csv"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aibot_displayer.settings")
django.setup()

from django.apps import apps

def clear_database():
    for model in apps.get_models():
        model.objects.all().delete()
        print(f"Cleared all data from {model._meta.label}.")

def reset_csv_file():
    # Path to your CSV file
    csv_path = CSV_PATH
    headers = ['hashkey', 'Date', 'Side', 'Asset', 'Price', 'Quantity', 'Total Dollars']
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
    print(f"Reset {csv_path} with headers.")

if __name__ == '__main__':
    clear_database()
    reset_csv_file()