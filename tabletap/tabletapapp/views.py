from django.shortcuts import render, get_object_or_404, redirect
from .models import UserDetail, Restaurant, MenuItem, Order, Table, Category, OrderItem
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.views.generic.edit import FormMixin
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.db.models import Q
from .forms import MenuItemForm, SignupForm, RestaurantForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth import login
from rest_framework import viewsets
from .serializers import MenuItemSerializer
from decimal import Decimal
from django.http import JsonResponse
import json

def index(request):
    return render(request, "index.html")


def login(request):
    return render(request, "login.html") 


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) 
            return redirect('index') 
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

@require_POST
def submit_order(request):
    restaurant_id = request.POST.get('restaurant_id')
    table_id = request.POST.get('table_id')
    cart_data = json.loads(request.POST.get('cart_data'))

    restaurant = Restaurant.objects.get(id=restaurant_id)
    table = Table.objects.get(id=table_id)

    total_cost = sum(item['price'] * item['quantity'] for item in cart_data)

    order = Order.objects.create(
        restaurant=restaurant,
        table=table,
        cost=total_cost
    )

    for item in cart_data:
        menu_item = MenuItem.objects.get(id=item['id'])
        OrderItem.objects.create(
            order=order,
            item=menu_item,
            quantity=item['quantity'],
            price=item['price']
        )

    return redirect('order_summary', order_id=order.id)


def order_summary(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    for item in order_items:
        item.subtotal = item.price * item.quantity
    context = {
        'order': order,
        'order_items': order_items,
    }

    return render(request, 'order_summary.html', context)

class MenuView(ListView):
    model = MenuItem
    template_name = 'menu.html'
    context_object_name = 'menu_items'
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant_id = self.request.GET.get("restaurant")
        table_num = self.request.GET.get("table")
        restaurant = Restaurant.objects.get(id=restaurant_id)
        table = Table.objects.get(table_num=table_num, restaurant=restaurant)
        context['restaurant'] = restaurant
        context['table'] = table

        categories = Category.objects.all()
        items_by_category = {
            category: MenuItem.objects.filter(restaurant=restaurant, category=category)
            for category in categories
        }
        context['items_by_category'] = items_by_category
        
        return context

@method_decorator(login_required, name='dispatch')
class ManageMenusView(ListView, FormMixin):
    model = MenuItem
    template_name = 'manage_menu.html'
    context_object_name = 'menu_items'
    paginate_by = 5
    form_class = RestaurantForm
    
    def get_queryset(self):
        try:
            self.restaurant = Restaurant.objects.get(owner=self.request.user)
        except Restaurant.DoesNotExist:
            self.restaurant = None
            return MenuItem.objects.none()
        
        queryset = super().get_queryset().filter(restaurant=self.restaurant)
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurant'] = self.restaurant
        
        if not self.restaurant:
            context['form'] = self.get_form()
        else:
            orders = Order.objects.filter(restaurant=self.restaurant)
            search_query = self.request.GET.get("search", "")
            if search_query:
                orders = orders.filter(table__table_num__icontains=search_query)
            context['orders'] = orders
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            form = self.get_form()
            if form.is_valid():
                new_table_count = form.cleaned_data['table_count']
                if new_table_count > restaurant.table_set.count():
                    for i in range(restaurant.table_set.count() + 1, new_table_count + 1):
                        Table.objects.create(restaurant=restaurant, table_num=i)
                elif new_table_count < restaurant.table_set.count():
                    Table.objects.filter(restaurant=restaurant, table_num__gt=new_table_count).delete()

                restaurant.name = form.cleaned_data['name']
                restaurant.table_count = new_table_count
                restaurant.save()

                for table in restaurant.table_set.all():
                    table.save()
                messages.success(request, "Restaurant updated successfully.")
            else:
                messages.error(request, "Please correct the errors.")
            return redirect('manage_menu')

        except Restaurant.DoesNotExist:
            form = self.get_form()
            if form.is_valid():
                restaurant = form.save(commit=False)
                restaurant.owner = request.user
                restaurant.save()
                for i in range(1, restaurant.table_count + 1):
                    Table.objects.create(restaurant=restaurant, table_num=i)
                messages.success(request, "Restaurant registered successfully.")
                return redirect('manage_menu')
            else:
                messages.error(request, "Please correct the errors.")
                return self.get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class MenuCreateView(CreateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'menu_form.html'
    success_url = reverse_lazy('manage_menu')

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['category'].queryset = Category.objects.all()
        return form
    
    def form_valid(self, form):
        from pprint import pprint
        restaurant = Restaurant.objects.get(owner=self.request.user)
        form.instance.restaurant = restaurant
        
        print("FILES:")
        pprint(self.request.FILES)
        print("cleaned_data:")
        pprint(form.cleaned_data)
        messages.success(self.request, "Item created successfully!")
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        from pprint import pprint
        print("FILES:")
        pprint(self.request.FILES)
        print("cleaned_data:")
        pprint(form.cleaned_data)
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class MenuUpdateView(UpdateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'menu_form.html'
    success_url = reverse_lazy('manage_menu')

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['category'].queryset = Category.objects.all()
        return form
    
    def form_valid(self, form):
        messages.success(self.request, "Item updated successfully!")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Something went wrong. Please check the form.")
        return super().form_invalid(form)

@method_decorator(login_required, name='dispatch')
class MenuDeleteView(DeleteView):
    model = MenuItem
    template_name = 'menu_confirm_delete.html'
    success_url = reverse_lazy('manage_menu')

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        restaurant = Restaurant.objects.get(owner=self.request.user)
        queryset = MenuItem.objects.filter(restaurant=restaurant)
        search = self.request.query_params.get('search')
        if search:
            return queryset.filter(search=search)
        return queryset

@method_decorator(login_required, name='dispatch')
class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'order_confirm_delete.html'
    success_url = reverse_lazy('manage_menu')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Order deleted successfully.")
        return super().delete(request, *args, **kwargs)

@method_decorator(login_required, name='dispatch')
class OrderFinishAjaxView(View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, table__restaurant__owner=request.user)
        order.is_finished = True
        order.save()
        return JsonResponse({"status": "finished"})

@method_decorator(login_required, name='dispatch')
class StaffMenuView(TemplateView):
    template_name = 'staff_menu.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            restaurant = Restaurant.objects.get(owner=self.request.user)
        except Restaurant.DoesNotExist:
            context['error'] = "No restaurant is associated with your account."
            return context

        context['restaurant'] = restaurant
        context['tables'] = Table.objects.filter(restaurant=restaurant)
        
        categories = Category.objects.all()
        items_by_category = {
            category: MenuItem.objects.filter(restaurant=restaurant, category=category)
            for category in categories
        }
        context['items_by_category'] = items_by_category

        return context
