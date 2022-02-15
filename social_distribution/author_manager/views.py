from django.contrib import messages
from django.shortcuts import redirect, render
from .forms import SignUpForm
from .models import Author
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)
            messages.success(request, 'Your account has been created!')
            return redirect('author_manager:login')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})     
           
def sign_in(request):
    if request.user.is_authenticated:
        return redirect('author_manager:home')
    form = AuthenticationForm()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=username, password=password)

            if user:
                login(request, user)
                return redirect('author_manager:home')
    return render(request, 'registration/login.html', {'form': form})


@login_required
def home(request):
    # this is temp we should probably do AJAX later
    return render(request, 'author_manager/index.html')