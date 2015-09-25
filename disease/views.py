from django.shortcuts import render

# Create your views here.
def diabetes(request):
    return render(request, "diabetes.html", {})
