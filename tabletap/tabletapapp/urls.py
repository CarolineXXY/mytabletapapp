from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    ManageMenusView,
    MenuCreateView,
    MenuUpdateView,
    MenuDeleteView,
    StaffMenuView,
    MenuItemViewSet,
    MenuView,
    OrderDeleteView,
    OrderFinishAjaxView,
)

router = DefaultRouter()
router.register(r'menuitems', MenuItemViewSet)

urlpatterns = [
    path("", views.index, name="index"),
    path("staff_menu/", StaffMenuView.as_view(), name="staff_menu"),
    path('menu/', MenuView.as_view(), name='menu'),
    path('accounts/', include('allauth.urls')),
    path('signup/', views.signup_view, name='signup'),
    path('api/', include(router.urls)),
    path("submit_order/", views.submit_order, name="submit_order"),
    path("order_summary/<int:order_id>/", views.order_summary, name="order_summary"),
    path("manage/", ManageMenusView.as_view(), name="manage_menu"),
    path("manage/add/", MenuCreateView.as_view(), name="menu_add"),
    path("manage/edit/<int:pk>/", MenuUpdateView.as_view(), name="menu_edit"),
    path("manage/delete/<int:pk>/", MenuDeleteView.as_view(), name="menu_delete"),
    path("manage/order/delete/<int:pk>/", OrderDeleteView.as_view(), name="order_delete"),
    path("manage/order/<int:pk>/finish-ajax/", OrderFinishAjaxView.as_view(), name="order_finish_ajax"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
