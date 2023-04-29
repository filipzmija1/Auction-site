from django.shortcuts import render
from django.views.generic import View, ListView, DeleteView
from django.contrib.auth import get_user_model

from .models import Auction, Item


User = get_user_model()


class StartPage(View):
    template_name = 'auctions/base_template.html'
    title = 'Auction house'
    auctions = Auction.objects.count()
    users = User.objects.count()

    def get(self, request):
        context = {
            'title': self.title,
            'auctions': self.auctions,
            'users': self.users
        }
        return render(request, self.template_name, context)


class ListItems(ListView):
    model = Item

