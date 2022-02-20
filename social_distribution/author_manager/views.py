from django.contrib import messages
from django.shortcuts import redirect, render
from .forms import SignUpForm
from .models import Author
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ProfileSerializer
from django.shortcuts import get_object_or_404
from rest_framework import status

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


class ProfileAPI(APIView):
    """
    An API endpoint allows viewing and updating a profile.
    ...
    Attributes:
    Methods:
        GET:
            Retrieve an author's profile.
        PUT:
            Update an author's profile.
    """
    def get(self, request, id):
        """
        Handling GET request. Showing the author's profile.
        Returns:
            - If successful:
                Status 200 and the author's basic information.
        """
        profile = Author.objects.get(id=id)
        # profile = get_object_or_404(Author, id=id)
        serializer = ProfileSerializer(profile, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetAllAuthors(APIView):
    def get(self, request):
        authors = Author.objects.all()
        serializer = ProfileSerializer(authors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)