import os
import requests
from django.shortcuts import render,redirect
from django.contrib import messages
from django.conf import settings
from .models import ProcessedPDF  # Import the ProcessedImage model


from django.contrib.auth.decorators import login_required
import time
import uuid


@login_required
def delete_document(request, file_id):

    if request.method == "POST":
        print("line 192", file_id)
        get_processed_file = ProcessedPDF.objects.filter(id=file_id).first()
        if get_processed_file:
            get_processed_file.delete()
            messages.success(request, "Document deleted successfully.")
            return redirect("processed_doc")  # Redirects to the home page
        else:
            # Handle the case where the file doesn't exist (e.g., raise a 404 or log the error)
            print("Processed file not found.")
            messages.error(request, "Document deleted Error.")
            return redirect("processed_doc")  # Redirects to the home page

    return redirect("processed_doc")

