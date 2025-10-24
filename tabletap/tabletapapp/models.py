from django.contrib.auth.models import User
from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from django.core.files.storage import default_storage
from PIL import Image, ImageDraw


class UserDetail(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('staff', 'Staff'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    table_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Restaurant: {self.name}, Owner: {self.owner.username}"
    
class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    table_num = models.IntegerField()
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)

    def __str__(self):
        return f"Table: {self.table_num} at {self.restaurant.name}"
    
    def save(self, *args, **kwargs):
        print(f"Saving Table {self.table_num} for Restaurant {self.restaurant.id}")
        fname = f'qr_code_r{self.restaurant.id}_t{self.table_num}.png'
        path = f'qr_codes/{fname}'

        if not self.qr_code or not default_storage.exists(path):
            menu_url = f"http://127.0.0.1:8000/tabletap/menu/?restaurant={self.restaurant.id}&table={self.table_num}"

            qr_img = qrcode.make(menu_url)
            canvas = Image.new('RGB', (250, 250), 'white')
            canvas.paste(qr_img.resize((250, 250)))

            buffer = BytesIO()
            canvas.save(buffer, format='PNG')
            buffer.seek(0)

            self.qr_code.save(fname, File(buffer), save=False)
            print("Saved QR code file to:", self.qr_code.name)
            buffer.close()

        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"

class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.category.name}) - ${self.price}"
    
class Order(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    is_finished = models.BooleanField(default=False) 
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Finished" if self.is_finished else "Pending"
        return f"Order #{self.id} - Status: {status}, Cost: ${self.cost}, Ordered at: {self.order_time.strftime('%d-%m-%Y %H:%M:%S')}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item.name} x {self.quantity} (Order: #{self.order.id})"