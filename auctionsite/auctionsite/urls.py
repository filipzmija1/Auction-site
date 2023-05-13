"""
URL configuration for auctionsite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django_email_verification import urls as mail_urls

import auctions.views as auctions

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', auctions.StartPage.as_view()),
    path('items/', auctions.ItemsList.as_view()),
    path('items/<int:pk>', auctions.ItemDetails.as_view()),
    path('auctions/', auctions.AuctionsList.as_view()),
    path('auction/<int:pk>', auctions.AuctionDetails.as_view()),
    path('add-auction/', auctions.AddAuction.as_view()),
    path('add-item', auctions.AddItem.as_view()),
    path('add-opinion/<int:pk>', auctions.AddOpinion.as_view()),
    path('bid-auction/<int:pk>', auctions.BidAuction.as_view()),
    path('search', auctions.SearchAuction.as_view()),
    path('edit-opinion/<int:pk>', auctions.EditOpinion.as_view()),
    path('login/', auctions.Login.as_view()),
    path('logout/', auctions.Logout.as_view()),
    path('create-account/', auctions.AddUser.as_view()),
    path('categories/', auctions.CategoriesList.as_view()),
    path('category/<slug:slug>', auctions.CategoryDetails.as_view()),
    path('user/<str:username>', auctions.UserProfile.as_view()),
    path('edit-profile/<int:pk>', auctions.EditUserProfile.as_view()),
    path('reset-password/<str:username>', auctions.ResetPassword.as_view()),
    path('bids/<int:pk>', auctions.BidHistory.as_view()),
    path('delete-opinion/<int:pk>', auctions.DeleteOpinion.as_view()),
    path('expired-auctions/', auctions.AuctionsList.as_view()),
    path('email/', include(mail_urls)),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
