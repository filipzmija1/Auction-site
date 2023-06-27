from django.contrib import admin
from .models import Item, Category, Auction, Opinion, Bid


admin.site.register(Item)
admin.site.register(Category)
admin.site.register(Auction)
admin.site.register(Opinion)
admin.site.register(Bid)