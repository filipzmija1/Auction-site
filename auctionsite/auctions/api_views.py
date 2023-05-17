from rest_framework import generics, viewsets

from django.contrib.auth import get_user_model

from .models import Auction, Opinion, Category, Item
from .serializers import AuctionSerializer, OpinionSerializer, CategorySerializer, ItemSerializer, UserSerializer


User = get_user_model()


class AuctionView(generics.ListAPIView):
    """Use generics for better readability"""
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer


class AuctionDetailView(generics.RetrieveAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer


class UserView(viewsets.ModelViewSet):
    """Use viewsets to stop reapeating code"""
    queryset = User.objects.all()
    serializer_class = UserSerializer


class OpinionView(viewsets.ModelViewSet):
    queryset = Opinion.objects.all()
    serializer_class = OpinionSerializer


class ItemView(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class CategoryView(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer