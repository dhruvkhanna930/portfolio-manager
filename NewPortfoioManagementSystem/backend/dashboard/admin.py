from django.contrib import admin
from .models import Portfolio, StockHolding, WalletTransaction, WatchlistItem

# Register your models here.
admin.site.register(Portfolio)
admin.site.register(StockHolding)
admin.site.register(WalletTransaction)
admin.site.register(WatchlistItem)