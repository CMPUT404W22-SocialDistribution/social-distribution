from email.errors import MessageError
import re
from django.contrib import messages
from django.shortcuts import redirect, render

# import idna
from .forms import SignUpForm, EditProfileForm
from .models import *
from django.contrib.auth import authenticate, login, logout
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
            inbox = Inbox(author=user.author)
            followers = FollowerList(author=user.author)
            inbox.save()
            followers.save()
            messages.success(request, 'Your account has been created.')
            return redirect('author_manager:login')
        else:
            errors = list(form.errors.values())
            for error in errors:
                mess = error[0] 
                break
            messages.warning(request, mess)
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
        else:
            messages.warning(request, 'Sorry, we could not find your account.')
    return render(request, 'registration/login.html', {'form': form})


@login_required
def home(request):
    # this is temp we should probably do AJAX later
    return render(request, 'author_manager/index.html')


@login_required
def sign_out(request):
    if request.method == 'GET':
        logout(request)
        print(request.user)
        return redirect('author_manager:login')

@login_required
def profile_edit(request, id):
    
    author = Author.objects.get(id=id)
    if request.user.author != author:
            error = "401 Unauthorized"
            return render(request, 'author_profile/edit_profile.html', {'error': error})
    if request.method == "GET":
        form = EditProfileForm(instance=author)
        return render(request, 'author_profile/edit_profile.html', {'form':form})
        # return render(request, 'author_profile/edit_profile.html', {'profile':author})
        
    elif request.method == "POST":
        updated_request = request.POST.copy()
        form = EditProfileForm(updated_request, instance=author)        
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('author_manager:profile', id)
        else:
            print(form.errors)
            return redirect('author_manager:editProfile', id)

@login_required
def friends_view(request, author_id):
    actor = Author.objects.get(id=author_id)

    if request.user.author != actor:
            return redirect('author_manager:login')

    if request.method == "GET":
        return render(request, 'friends/friends.html')

    elif request.method == "POST":
        object_id = request.POST.get('object_id')

        if object_id == author_id:
            messages.warning(request, 'You cannot be friend with yourself')
            return redirect('author_manager:friends', author_id)

        try:
            object = Author.objects.get(id=object_id)
            
            try:
                friend_request = FriendRequest.objects.get(actor=actor, object=object)
                messages.warning(request, 'You already sent a friend request to this author.')
                return redirect('author_manager:friends', author_id)
            
            except FriendRequest.DoesNotExist:
                friend_request = FriendRequest(actor=actor, object=object)
                friend_request.save()

                inbox = Inbox.objects.get(author=object)
                inbox.follows.add(friend_request)

                messages.success(request, 'Your friend request has been sent.')
                return redirect('author_manager:friends', author_id)

        except Author.DoesNotExist:
            messages.warning(request, 'Sorry, we could not find this author.')
            return redirect('author_manager:friends', author_id)


@login_required
def inbox_view(request, author_id):
    current_author = Author.objects.get(id=author_id)

    if request.user.author != current_author:
            return redirect('author_manager:login')

    if request.method == "GET":
        inbox = Inbox.objects.get(author=current_author)
        return render(request, 'inbox/inbox.html', {'follows' : inbox.follows.all()})
    
    # if request.method == "POST":
    #     if request.POST['type'] == 'follows':

    return render(request, 'inbox/inbox.html')


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

    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'author_profile/profile.html'

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
        return Response({'profile': profile})
        # return Response(serializer.data, status=status.HTTP_200_OK)

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
