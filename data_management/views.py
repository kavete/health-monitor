from django.shortcuts import render

def dashboard(request):
    context = {}
    return render(request, 'data_management/index.html', context)


def ward_details(request):
    context = {}
    return render(request, 'data_management/ward-details.html', context)