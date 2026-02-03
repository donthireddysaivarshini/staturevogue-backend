from django.urls import path
from .views import WebContentPublicView

urlpatterns = [
    path('public/', WebContentPublicView.as_view(), name='public-content'),
]