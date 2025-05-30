from django.shortcuts import render

def dashboard(request):
    context = {}
    return render(request, 'data_management/index.html', context)
