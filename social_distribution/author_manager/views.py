from django.contrib import messages
from django.shortcuts import redirect, render
from .forms import SignUpForm
from .models import Author
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
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
    Methods:
        GET:
            Retrieve given author's profile.
        POST:
            update an author's profile.
    """

    # renderer_classes = [TemplateHTMLRenderer]
    # template_name = 'author_profile/profile.html'

    def get(self, request, id):
        """
        Handling GET request. Showing the author's profile.
        Returns:
            - If successful:
                Status 200 and the author's basic information.
        """
        profile = Author.objects.get(id=id)
        # profile = get_object_or_404(Author, id=id)
        serializer = ProfileSerializer(profile, remove_fields=['user'] )
        # return Response({'profile': profile})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, id):
        #Get object we want to update
        profile = Author.objects.get(id=id)
        serializer = ProfileSerializer(profile, data=request.data, partial=True, remove_fields=['user'])

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            response = {
                "status": 1,
                "message": serializer.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

class GetAllAuthors(APIView):
    """
    An API endpoint allows viewing all author's profile
    ...
    Methods:
        GET:
            Retrieve all author's profiles
    """
    def get(self, request):
        """
        Handling GET request. Showing all author's profiles.
        Returns:
            - If successful:
                Status 200 and the author's basic information.
        """
        authors = Author.objects.all()
        serializer = ProfileSerializer(authors, many=True, remove_fields=['user'])
        response = {
            'type':  "authors",
            'items': serializer.data
        }
        return Response(response, status=status.HTTP_200_OK)