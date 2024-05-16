from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from .models import historyStorage
from django.db.models import Sum, F, ExpressionWrapper, FloatField, Case, When, Value, FloatField, Subquery, OuterRef
from django.db.models.functions import Coalesce
import pandas as pd
import csv
from datetime import datetime
from django.utils.timezone import make_aware
import os
# Create your views here.

CSV_PATH  = "D:/VVWoodworks Market Trader/AI-Bot-Trader/trace.csv"
def homepage(request):
    introduction()
    return render(request = request,
                  template_name='main/home.html',
                  context = {"tutorials":False})

def introduction():
    import_trades_from_csv(CSV_PATH)
    allocate_sales()

from django.db.models import Case, When, Value, FloatField, Subquery, OuterRef

def current_holdings(request):
    introduction() 
    buys = historyStorage.objects.filter(asset_buydate__isnull=False, asset_selldate__isnull=True).order_by('asset_title', 'asset_buydate')
    solds = historyStorage.objects.filter(asset_buydate__isnull=False, asset_qtysold__gt=0).order_by('asset_title', 'asset_buydate')

    wallet = {}  # Dictionary to store wallet information
    bankmade = {}
    for buy in buys:
        security_name = buy.asset_title
        current_qty_count = buy.asset_qty - buy.asset_qtysold
        total_cost = current_qty_count * buy.asset_price
        
        # Update wallet dictionary for the current security
        if security_name in wallet:
            # If security already exists in the wallet, update total quantity and cost
            wallet[security_name]['total_qty'] += current_qty_count
            wallet[security_name]['total_cost'] += total_cost
            wallet[security_name]['date'] = buy.asset_buydate
        else:
            # If security is new, create a new entry in the wallet dictionary
            wallet[security_name] = {
                'security_name': security_name,
                'total_qty': current_qty_count,
                'total_cost': total_cost
            }
    for sold in solds:
        security_name = sold.asset_title
        soldqty = sold.asset_qtysold
        soldprice = sold.asset_soldprice
        soldtotal = float(soldprice *soldqty)
        soldhash = sold.hash_field
        if security_name in bankmade:
            bankmade[security_name][soldhash]['date']= sold.asset_selldate
            bankmade[security_name][soldhash]['qty_sold']= soldqty
            bankmade[security_name][soldhash]['sell_price'] = soldprice
            bankmade[security_name][soldhash]['sell_total'] = soldtotal
        else:
             wallet[security_name][soldhash] = {
                'date': sold.asset_selldate,
                'security_name': security_name,
                'qty_sold': soldqty,
                'sell_price': soldprice,
                'sell_total': soldtotal
            }   

        print(bankmade) ##################this is blank for somereason - need this to _NOT_ be blank


    return JsonResponse({'wallet': wallet, 'bankmade': bankmade})


def history_data(request):
    # Assuming you pass 'date' in the request, e.g., '2023-01-01'
    query_date = request.GET.get('date')

    if not query_date:
        return JsonResponse({'error': 'Date parameter is required'}, status=400)

    # Get transactions for a specific date
    data = historyStorage.objects.filter(
        asset_buydate__date=query_date
    ).annotate(
        daily_cost=ExpressionWrapper(F('asset_qty') * F('asset_price'), output_field=FloatField()),
        daily_sold=ExpressionWrapper(F('asset_qtysold') * F('asset_soldprice'), output_field=FloatField())
    ).aggregate(
        total_cost=Sum('daily_cost'),
        total_sold=Sum('daily_sold'),
        total_profit=Sum(Coalesce('daily_sold', 0) - Coalesce('daily_cost', 0))
    )

    return JsonResponse(data)

def trades(request):
    # Fetch all trades from the database
    trades = historyStorage.objects.all()
    # Prepare data to match the expected JSON structure
    trades_list = [
        {
            'Date': trade.asset_buydate.strftime('%Y-%m-%d') if trade.asset_buydate else trade.asset_selldate.strftime('%Y-%m-%d'),
            'Side': 'buy' if trade.asset_buydate else 'sell',
            'Asset': trade.asset_title,
            'Price': trade.asset_price,
            'Quantity': trade.asset_qty,
            'Total Dollars': trade.asset_totaldollars
        }
        for trade in trades
    ]
    # Return the data as JSON
    return JsonResponse(trades_list, safe=False)

def last_modified(request):
    mod_time = os.path.getmtime(CSV_PATH)
    return JsonResponse({'last_modified': mod_time})

def import_trades_from_csv(csv_path):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        entries_to_add = []
        for row in sorted(reader, key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d')):
            # Extract data from CSV row
            hash_key = row['hashkey']
            asset_title = row['Asset']
            asset_qty = int(float(row['Quantity']))
            asset_totaldollars = float(row['Total Dollars'])
            asset_price = float(row['Price'])
            date_format = "%Y-%m-%d"
            asset_date = make_aware(datetime.strptime(row['Date'], date_format))
            
            # Check if hash_key already exists in the database
            if not historyStorage.objects.filter(hash_field=hash_key).exists():
                # Create a new entry object and add it to the list
                entry = historyStorage(
                    asset_title=asset_title,
                    asset_qty=asset_qty,
                    asset_price = asset_price,
                    asset_totaldollars=asset_totaldollars,
                    hash_field=hash_key
                )
                # Set buy or sell date based on 'Side'
                if row['Side'].lower() == 'buy':
                    entry.asset_buydate = asset_date
                else:
                    entry.asset_selldate = asset_date
                
                entries_to_add.append(entry)

        # Bulk create all new entries
        historyStorage.objects.bulk_create(entries_to_add)
        print(f"Added {len(entries_to_add)} new entries to the database.")

def allocate_sales():
    # Get all sales sorted by sell date
    sales = historyStorage.objects.filter(asset_selldate__isnull=False, asset_sell_considered=False).order_by('asset_selldate')


    # Get all buys sorted by buy date
    buys = list(historyStorage.objects.filter(asset_buydate__isnull=False, asset_selldate__isnull=True).order_by('asset_buydate'))

    # Loop through each sale
    for sale in sales:
        quantity_to_allocate = sale.asset_qty

        # Loop through each buy to allocate the sold quantity
        for buy in buys:
            if quantity_to_allocate <= 0:
                break  # Stop if all sold quantity has been allocated

            if buy.asset_qtysold < buy.asset_qty:
                available_qty = buy.asset_qty - buy.asset_qtysold
                allocation = min(available_qty, quantity_to_allocate)
                buy.asset_qtysold += allocation
                buy.asset_soldprice = sale.asset_price  # Using the sale price from the sale record
                buy.save(update_fields=['asset_qtysold', 'asset_soldprice'])
                quantity_to_allocate -= allocation

        # If not all sale quantity could be allocated, handle the shortage
        if quantity_to_allocate > 0:
            print(f"Warning: Not enough inventory to cover the sale of {quantity_to_allocate} units for {sale.asset_title} on {sale.asset_selldate}")
        if quantity_to_allocate == 0:
            sale.asset_sell_considered = True
            sale.save(update_fields=['asset_sell_considered'])
# This function should be called appropriately within your application logic
