from datetime import datetime
from PIL import Image
from io import BytesIO

from django.forms.models import BaseModelForm
from django.shortcuts import render, redirect
from django.views.generic import View, ListView, CreateView, DeleteView
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings

from django_email_verification import send_email
from twilio.rest import Client

from .models import Auction, Item, Opinion, Bid, Category, Account
from .utils import average_rating
from .forms import BidForm, OpinionForm, SearchForm, LoginForm, AddUserForm, ResetPasswordForm, AddAuctionForm, \
    EditUserForm, EditOpinionForm



User = get_user_model()


class StartPage(View):
    """This view shows the start page of the auction house"""
    template_name = 'auctions/base_template.html'
    title = 'Auction house'
    
    def get(self, request):
        users = User.objects.count()
        auctions = Auction.objects.count()
        context = {
            'title': self.title,
            'auctions': auctions,
            'users': users,
        }
        return render(request, self.template_name, context)


class ItemsList(ListView):
    """Shows a list of all available items"""
    model = Item
    paginate_by = 10


class ItemDetails(View):
    """This view shows the details of particural item"""
    template_name = 'auctions/item_detail.html'

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']   # Get the primary key of the item from the URL
        item = Item.objects.get(pk=pk)
        context = {
            'item': item,
            }
        return render(request, self.template_name, context)


class AuctionsList(ListView):
    """Shows a list of all auctions"""
    model = Auction
    context_object_name = 'auction_list'
    paginate_by = 5

    def get_context_data(self, **kwargs):
        """Method is used to change auction status after expired or sold"""
        context = super().get_context_data(**kwargs)    # Get default context data
        for auction in context['auction_list']:
            if auction.end_date < timezone.now() and auction.bid_set.count() > 0:
                auction.status = 'sold'
                auction.save()
            elif auction.end_date < timezone.now():   # Check if end date is past
                auction.status = 'expired'
                auction.save()
        return context

    def get_template_names(self, **kwargs):
        """Method is used to dynamically determine the template to use based on the 'status' parameter in the URL"""
        status = self.request.GET.get('status')     # Get status parameter from the request
        if status == 'expired':
            return 'auctions/expired_auction_list.html'
        elif status == 'available':
            return 'auctions/available_auction_list.html'
        elif status == 'sold':
            return 'auctions/sold_auction_list.html'
        else:
            return 'auctions/auction_list.html'


class AuctionDetails(View):
    """This view shows the details (includes opinions) of particural auction"""
    template_name = 'auctions/auction_detail.html'

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']   # Get the primary key of the auction from the URL
        auction = Auction.objects.get(pk=pk)
        opinions = auction.opinion_set.all().order_by('-date_created')
        paginator = Paginator(opinions, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        ratings = []
        for opinion in opinions:
            ratings.append(opinion.rating)  # Get every rating from opinion
        average_rate = average_rating(ratings)  # Count average rating
        context = {
            'auction': auction,
            'opinions': page_obj,
            'average_rating': average_rate,
        }
        return render(request, self.template_name, context)


class CategoriesList(ListView):
    """Shows names and descriptions of categories"""
    model = Category


class CategoryDetails(View):
    """Shows category details include category items"""
    def get(self, request, *args, **kwargs):
        slug = kwargs['slug']   # Get category name from URL
        category = Category.objects.get(name=slug)
        items = category.item_set.all()
        context = {
            'category': category,
            'items': items
        }
        return render(request, 'auctions/category_detail.html', context)


class AddAuction(LoginRequiredMixin, CreateView):
    """This view creates new auction (prefer to create item before creating auction)"""
    template_name = 'auctions/auction_form.html'

    def get(self, request, *args, **kwargs):
        form = AddAuctionForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = AddAuctionForm(request.POST, user=request.user)
        if form.is_valid():
            name = form.cleaned_data['name']
            item = form.cleaned_data['item']
            min_price = form.cleaned_data['min_price']
            buy_now_price = form.cleaned_data['buy_now_price']
            end_date = form.cleaned_data['end_date']
            user = request.user
            if buy_now_price:
                if min_price > buy_now_price:
                    messages.error(request, 'Price without bidding cannot be less than minimum price')
                    return redirect('/add-auction')
            if end_date < timezone.now():   # Check if date is not past
                messages.error(request, 'End date cannot be past')
                return redirect('/add-auction')
            else:
                Auction.objects.create(name=name,
                                       item=item,
                                       min_price=min_price,
                                       buy_now_price=buy_now_price,
                                       end_date=end_date,
                                       seller=user)
                return redirect('/auctions')
        else:
            return render(request, self.template_name, {'form': self.form})


class BuyNow(LoginRequiredMixin, View):
    """This view is used to buy auction item without bidding (only if auction allows that)"""
    template_name = 'auctions/buy_auction_now.html'

    def get(self, request, *args, **kwargs):
        auction_id = kwargs['pk']
        auction = Auction.objects.get(id=auction_id)
        user = request.user
        if user.id == auction.seller.id:
            messages.error(request, 'You cannot buy your own auction')
            return redirect(f'/auction/{auction.id}')
        if auction.bid_set.count() > 0: # Check if someone started bidding auction
            messages.error(request, 'You cannot buy right now because someone started to bid on auction already'
                                    ' (you can bid too)')
            return redirect(f'/auction/{auction.id}')
        if auction.status == 'available':
            if not auction.buy_now_price:
                raise Http404('You can not do this because auction has no price without bid')
            else:
                return render(request, self.template_name, {'auction': auction})
        else:
            messages.error(request, 'Buy item from expired or sold auction is not allowed')
            return redirect(f'/auction/{auction.id}')

    def post(self, request, *args, **kwargs):
        auction_id = kwargs['pk']
        auction = Auction.objects.get(id=auction_id)
        auction.status = 'sold'
        auction.buyer = request.user
        auction.save()
        messages.success(request, f'Congratulation! You bought {auction.item.name} from {auction.name}')
        return redirect('/auctions')


class AddItem(LoginRequiredMixin, CreateView):
    """This view creates new item that should be used in creating auction"""
    model = Item
    fields = ['name', 'description', 'image', 'category']
    template_name = 'auctions/item_form.html'
    success_url = '/items'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class AddOpinion(LoginRequiredMixin, View):
    """View destined to add new opinions about auctions"""
    template_name = 'auctions/opinion_form.html'

    def get(self, request, *args, **kwargs):    # Handle GET request to display the opinion form
        form = OpinionForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = OpinionForm(request.POST)
        pk = kwargs['pk']
        auction = Auction.objects.get(pk=pk)
        if form.is_valid():     # If form is valid create a new Opinion object and redirect to auction detail page
            reviewer = request.user
            comment = form.cleaned_data['comment']
            rating = form.cleaned_data['rating']
            Opinion.objects.create(auction=auction, reviewer=reviewer, rating=rating, comment=comment)
            messages.success(request, 'Added opinion successfully')
            return HttpResponseRedirect(f'/auction/{auction.id}')
        else:   # If form is not valid render the opinion form again with the validation errors
            return render(request, self.template_name, {'form': form})


class EditOpinion(LoginRequiredMixin, View):
    """This view edits opinion"""
    template_name = 'auctions/opinion_edit.html'

    def get(self, request, *args, **kwargs):
        opinion_id = kwargs['pk']   # Get opinion id from the URL
        opinion = Opinion.objects.get(pk=opinion_id)
        form = EditOpinionForm(instance=opinion)
        user = request.user
        context = {
            'form': form,
            'opinion': opinion
        }
        if opinion.reviewer.id != user.id:
            raise PermissionDenied
        else:
            return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        opinion_id = kwargs['pk']  # Get opinion id from the URL
        opinion = Opinion.objects.get(pk=opinion_id)
        form = EditOpinionForm(request.POST)
        auction_id = opinion.auction.id
        if form.is_valid():
            opinion.rating = form.cleaned_data['rating']
            opinion.comment = form.cleaned_data['comment']
            opinion.date_edited = datetime.now()
            opinion.save()
            messages.success(request, 'Opinion changed successfully')
            return redirect(f'/auction/{auction_id}')


class DeleteOpinion(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """This view deletes opinion"""
    model = Opinion
    success_message = 'Opinion deleted successfully'

    def get_success_url(self):
        """This method get the success URL from opinion id"""
        user = self.request.user    # Get logged user
        opinion_id = self.kwargs.get('pk')  # Get opinion id from the URL
        opinion = Opinion.objects.get(id=opinion_id)
        auction = opinion.auction
        if user.id != opinion.reviewer.id:
            raise PermissionDenied
        else:
            return f'/auction/{auction.id}'


class BidAuction(LoginRequiredMixin, View):
    """The view destined to bid on auctions (if bid is 20 minutes before end of auction,
      it increases end of auction time for 20 minutes). It sends SMS and email to a person whose has been outbid """
    form = BidForm()
    context = {}
    template_name = 'auctions/bid_form.html'

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        auction = Auction.objects.get(id=pk)
        self.context['auction'] = auction
        self.context['form'] = self.form
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        form = BidForm(request.POST)
        pk = kwargs['pk']
        auction = Auction.objects.get(id=pk)
        account_sid = 'AC449aac404a7f04f5504ce0f19a97d237'  # account sid used to send SMS
        auth_token = '832c05a0407d124bb5b7c55cbcc8ef01'     # account auth_token used to send SMS
        client = Client(account_sid, auth_token)
        bidder = request.user
        if form.is_valid():
            if auction.buyer == request.user:
                messages.error(request, 'You cannot bid because last person who bids is you!')
                return redirect(f'/auction/{auction.id}')
            if auction.seller == request.user:
                messages.error(request, 'You cannot bid on your own auction!')
                return redirect(f'/auction/{auction.id}')
            if auction.status == 'expired' or auction.status == 'sold':
                messages.error(request, 'Bid on expired or sold auctions is not allowed!')
                return redirect(f'/auction/{auction.id}')
            new_price = form.cleaned_data['amount']
            
            if auction.min_price >= new_price:  # Check if new price is bigger than minimum price of the auction
                messages.error(request, 'New price cannot be equal or less than minimum price!')
                return render(request, self.template_name, self.context)
            else:
                if timezone.now() + timezone.timedelta(minutes=20) > auction.end_date:
                    auction.end_date += timezone.timedelta(minutes=20)
                if auction.buyer:
                    outbided_account = Account.objects.get(user=auction.buyer) # Get account for send SMS
                    if outbided_account.phone_number:
                        message = client.messages.create(
                            body=f'Your auction: "{auction.name}" has been outbid. New price is {new_price}!',
                            from_='+12543544729',
                            to='+48{}'.format(outbided_account.phone_number)
                        )
                send_mail(f'{auction.name}',    # Sends email to outbid person
                                  f'You have been outbid. New price is {new_price}',
                                   f'{settings.EMAIL_HOST_USER}',
                                   [f'{auction.buyer.email}'])  
                auction.min_price = new_price
                auction.buyer = bidder
                auction.save()
                Bid.objects.create(amount=new_price, auction=auction, bidder=bidder)
            messages.success(request, 'Bid successfully')  # Display success and redirect to the auction details page
            return redirect(f'/auction/{auction.id}')
        else:
            return render(request, self.template_name, self.context)


class BidHistory(View):
    """Shows every bid for auction"""
    def get(self, request, *args, **kwargs):
        auction_id = kwargs['pk']  # Get auction id from the URL
        auction = Auction.objects.get(pk=auction_id)
        bids = auction.bid_set.all().order_by('-time')
        context = {
            'auction': auction,
            'bids': bids,
        }
        return render(request, 'auctions/bid_history_list.html', context)


class SearchAuction(View):
    """This view is destined to search auction, category or item by name"""
    template_name = 'auctions/search_form.html'

    def get(self, request, *args, **kwargs):
        form = SearchForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = SearchForm(request.POST)
        context = {
            'form': form,
        }
        if form.is_valid():
            search = form.cleaned_data['search']    # Get search query from form
            item_results = Item.objects.filter(Q(name__icontains=search) | Q(name__startswith=search))
            auction_result = Auction.objects.filter(Q(name__icontains=search) | Q(name__startswith=search))
            category_result = Category.objects.filter(Q(name__icontains=search) | Q(name__startswith=search))
            if not item_results and not auction_result and not category_result:
                messages.error(request, 'Didnt match any result')   # If no results found display error message
                return render(request, self.template_name, context)
            else:   # If results found display them
                context['item_result'] = item_results
                context['auction_result'] = auction_result
                context['category_result'] = category_result
                return render(request, self.template_name, context)


class Login(View):
    template_name = 'auctions/login_form.html'

    def get(self, request, *args, **kwargs):
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            next_url = request.GET.get('next')  # Get next page from URL
            if user:    # If user is authenticated log in and redirect to home page
                login(request, user)
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect(f'/user/{user.username}')
            else:
                form.add_error(None, 'Invalid username or password')
                return render(request, self.template_name, {'form': form})


class Logout(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('/home')


class AddUser(View):
    """View that creates new user and login after valid form"""
    form = AddUserForm()
    template_name = 'auctions/add_user_form.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': self.form})

    def post(self, request, *args, **kwargs):
        form = AddUserForm(request.POST)
        users = User.objects.all()  # Retrieve all users data
        usernames = []
        emails = []
        for user in users:  # Getting usernames and emails
            usernames.append(user.username)
            emails.append(user.email)
        if form.is_valid():
            username = form.cleaned_data['username']
            confirm_password = form.cleaned_data['confirm_password']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            if username in usernames:   # Check if username already exists
                form.add_error(None, 'User already exists')
            elif password != confirm_password:
                form.add_error(None, 'Passwords do not match')
            elif email in emails:   # Check if email already exists
                form.add_error(None, 'Email is already in used')
            else:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email)
                user.is_active = False
                Account.objects.create(user=user)
                send_email(user)    # Send email to verify account
                messages.success(request, 'Check email to enable your account')
                return redirect('/home')
        return render(request, self.template_name, {'form': form})


class UserProfile(View):
    """This view shows user data (if user is created by all-auth library it creates extra account fields)"""
    def get(self, request, *args, **kwargs):
        username = kwargs['username']   # Get user profile from the URL
        user = User.objects.get(username=username)  # Get user data
        bids = Bid.objects.filter(bidder=user).order_by('-time')  # Get every user bids
        paginator = Paginator(bids, 3)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'user': user,
            'bids': page_obj,
        }
        try:
            user_account = Account.objects.get(user=user)
            context['user_account'] = user_account
            return render(request, 'auctions/user_profile.html', context)
        except:
            user_account = Account.objects.create(user=user)
            context['user_account'] = user_account
            return render(request, 'auctions/user_profile.html', context)

class EditUserProfile(LoginRequiredMixin, SuccessMessageMixin, View):
    """This view edits user profile"""
    template_name = 'auctions/edit_user_profile.html'

    def get(self, request, *args, **kwargs):
        user_id = kwargs['pk']  # Get id from the URL
        user = request.user
        user_account = Account.objects.get(user=user)
        form = EditUserForm(initial={
            'first_name':user.first_name,
            'last_name':user.last_name,
            'phone_number':user_account.phone_number})
        if user_id != user.id:
            raise PermissionDenied
        else:
            return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = EditUserForm(request.POST)
        user = request.user
        user_account = Account.objects.get(user=user)
        if form.is_valid():     # Check if form is valid
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user_account.phone_number = form.cleaned_data['phone_number']
            user_account.save()
            user.save()
            messages.success(request, 'Account data changed successfully')
            return redirect(f'/user/{user.username}')
        else:   # If form is not valid return form with errors
            return render(request, self.template_name, {'form': form})


class ResetPassword(LoginRequiredMixin, View):
    """Reset logged user password"""
    template_name = 'auctions/reset_password_form.html'
    form = ResetPasswordForm()

    def get(self, request, *args, **kwargs):
        username = kwargs['username']  # Get user username from the URL
        user = request.user
        if user.username != username:
            raise PermissionDenied
        else:
            return render(request, self.template_name, {'form': self.form})

    def post(self, request, *args, **kwargs):
        form = ResetPasswordForm(request.POST)
        user = request.user
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully')
                return redirect('/home')
        messages.error(request, 'Passwords do not match')
        return render(request, self.template_name, {'form': self.form})


class DeleteUser(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """This view allows user to delete his own profile"""
    model = User
    success_message = 'Your account has been deleted successfully'
    template_name = 'auctions/user_confirm_delete.html'
    
    def get_success_url(self):
        user = self.request.user    # Get logged user
        user_id = self.kwargs.get('pk') # Get user id from the URL
        if user.id != user_id:
            raise PermissionDenied
        else:
            return '/home'