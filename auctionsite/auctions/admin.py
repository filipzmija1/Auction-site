from django.contrib import admin
from .models import Item, Category, Auction, Opinion


admin.site.register(Item)
admin.site.register(Category)
admin.site.register(Auction)
admin.site.register(Opinion)
