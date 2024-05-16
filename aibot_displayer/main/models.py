from django.db import models


class historyStorage(models.Model):
    asset_title = models.CharField(max_length=200)
    asset_qty = models.IntegerField()
    asset_buydate = models.DateTimeField(null=True, blank=True)  # Changed for clarity
    asset_price = models.FloatField()
    asset_selldate = models.DateTimeField(null=True, blank=True)  # Changed to allow null
    asset_totaldollars = models.FloatField()
    asset_qtysold = models.IntegerField(default = 0)
    asset_soldprice = models.FloatField(default = 0.0)
    asset_sell_considered = models.BooleanField(default= False)
    hash_field = models.CharField(max_length=64) 
    

