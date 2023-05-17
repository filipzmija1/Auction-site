from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Auction, Opinion, Item, Category, Account


User = get_user_model()


class AuctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auction
        fields = ['id', 'name', 'item', 'min_price', 'buy_now_price', 'end_date', 'seller', 'buyer', 'status']


class OpinionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Opinion
        fields = ['id', 'auction', 'reviewer', 'rating', 'comment', 'date_created', 'date_edited']


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'image', 'category']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class UserSerializer(serializers.ModelSerializer):
    """Get user and his account data(phone_number)"""
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number']


    def get_phone_number(self, obj):
        return obj.account.phone_number