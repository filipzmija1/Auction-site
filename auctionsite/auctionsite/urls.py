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
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

import auctions.views as auctions
import auctions.api_views as api_views


router = DefaultRouter()
router.register('users', api_views.UserView)
router.register('opinions', api_views.OpinionView)
router.register('items', api_views.ItemView)
router.register('categories', api_views.CategoryView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', auctions.StartPage.as_view()),
    path('items/', auctions.ItemsList.as_view()),
    path('items/<uuid:pk>', auctions.ItemDetails.as_view()),
    path('auctions/', auctions.AuctionsList.as_view()),
    path('auction/<uuid:pk>/', auctions.AuctionDetails.as_view(), name='auction-detail'),
    path('add-auction/', auctions.AddAuction.as_view()),
    path('add-item/', auctions.AddItem.as_view()),
    path('add-opinion/<int:pk>', auctions.AddOpinion.as_view()),
    path('bid-auction/<int:pk>', auctions.BidAuction.as_view()),
    path('search', auctions.SearchAuction.as_view()),
    path('edit-opinion/<int:pk>', auctions.EditOpinion.as_view()),
    path('logout/', auctions.Logout.as_view()),
    path('create-account/', auctions.AddUser.as_view()),
    path('categories/', auctions.CategoriesList.as_view()),
    path('category/<slug:slug>/', auctions.CategoryDetails.as_view()),
    path('user/<str:username>', auctions.UserProfile.as_view()),
    path('edit-profile/<int:pk>', auctions.EditUserProfile.as_view()),
    path('reset-password/<str:username>', auctions.ResetPassword.as_view()),
    path('bids/<int:pk>', auctions.BidHistory.as_view()),
    path('delete-opinion/<int:pk>', auctions.DeleteOpinion.as_view()),
    path('expired-auctions/', auctions.AuctionsList.as_view()),
    path('email/', include(mail_urls)),
    path('buy-now/<uuid:pk>', auctions.BuyNow.as_view(), name='buy-now'),
    path('delete-user/<int:pk>', auctions.DeleteUser.as_view()),
    
    path('reset_password/', auth_views.PasswordResetView.as_view(
    template_name='auctions/account/password_reset.html')
         , name='reset_password'),

    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(
    template_name='auctions/account/password_reset_form.html'),
          name='password_reset_confirm'),

    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(
    template_name='auctions/account/password_reset_send.html')
         , name='password_reset_done'),

    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(
    template_name='auctions/account/password_reset_done.html'),
          name='password_reset_complete'),

    path('accounts/', include('allauth.urls')),
    
    path('api/auctions/', api_views.AuctionView.as_view()),
    path('api/auctions/<int:pk>', api_views.AuctionDetailView.as_view()),
    path('api/', include((router.urls, 'api'))),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
