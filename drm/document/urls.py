from django.urls import path
from . import views

urlpatterns = [
    path("delete/<int:file_id>/", views.delete_document, name="delete_document"),
]
