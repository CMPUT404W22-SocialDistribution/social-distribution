from doctest import Example
from email import message
from email.errors import MessageError
import stat
from urllib import response
from django.contrib import messages
from django.views.generic import ListView
from django.shortcuts import redirect, render
from django.db.models import Q
from .forms import SignUpForm, EditProfileForm
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework import generics, authentication, permissions
from .serializers import *
from django.shortcuts import get_object_or_404
from rest_framework import status
import requests
import datetime 

def sign_up(request):
    '''
    The function defines a view that allows account creation

    Method:
        POST:   - check if data is valid using default form set.
                - set user's active status to False upon save.
                - create an Inbox object for each Author user.
    '''

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)
            if 'HTTP_POST' in request.META:
                user.author.host =  request.scheme + '://' + request.META['HTTP_HOST'] + '/'
                user.author.url = user.author.host + 'authors/' + str(user.author.id)
                user.author.save()
            else: 
                user.author.host = request.get_host()
                user.author.url = user.author.host + 'authors/' + str(user.author.id)
                user.author.save()
            inbox = Inbox(author=user.author)  # create inbox object
            inbox.save()
            messages.success(request, 'Your account has been created.')
            return redirect('author_manager:login')  # redirects back to login page
        else:
            errors = list(form.errors.values())
            for error in errors:
                mess = error[0] 
                break
            messages.warning(request, mess)  
    else:
        form = SignUpForm()  # get form
    return render(request, 'registration/signup.html', {'form': form})     
           
def sign_in(request):
    '''
    The function defines a view that allows user to login

    Method:
        POST:   - checks if data is valid using default form set.
                - signs user into a session with Django session cookie.
    '''

    if request.user.is_authenticated:
        # check if user already authenticated, if so redirects to homepage 
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
            # if the authentication fails, get the same template form
            messages.warning(request, 'Sorry, we could not find your account.')
    return render(request, 'registration/login.html', {'form': form})


@login_required
def home(request):
    '''
    The function gets homepage view. Require authorization.
    '''
    if request.method == "GET":
        author = get_object_or_404(Author, user=request.user)  # get author objects of logged in Django user
        # get counts of followers, following, and friends to display in homepage
        followers = author.followers.all()
        followings = author.followings.all()
        friends = followings & followers
        return render(request, 'author_manager/index.html', {'author': author, 'friends_count': friends.count})


@login_required
def sign_out(request):
    '''
    The function logs out the authenticated user, and cleans out the session data. Require authorization.
    Redirect to login page.
    '''
    if request.method == 'GET':
        logout(request)
        return redirect('author_manager:login')


@login_required
def friends_view(request, author_id):
    '''
    The functions define a view that allow the author_id to view their followers, followings and true (bidirection) friends.
    The view also allows the author_id to access searching authors and unfriend (unfolllow) with other authors.
    Require authorization.

    Method:
        GET:    - the view of friends page that display the author_id's followings, followers and friends
        POST:   - unfriend with the requested_author

    '''
    current_author = Author.objects.get(id=author_id)
    if request.method == "GET":
        followers = current_author.followers.all()
        followings = current_author.followings.all()
        friends = followings & followers
        return render(request, 'friends/friends.html', {'followings': followings, 'followers': followers, 'friends': friends})
    
    if request.method == "POST":
        requested_id = request.POST['object_id']
        try:
            requested_author = get_object_or_404(Author, id=requested_id)
            current_author.followings.remove(requested_author)
            requested_author.followers.remove(current_author)

            mess = 'Your are now unfriend with ' + requested_author.displayName
            messages.success(request, mess)
            return redirect('author_manager:friends', author_id)
        except:
            return redirect('author_manager:friends', author_id)

class SearchAuthorView(ListView):
    '''
    The class define a result view of searching for authors as well as allow sending friend request to the found authors 

    Method:
        GET:    - filter authors by username/displayName with the given input
        POST:   - send a friend request to the requested_id
    '''
    model = Author
    template_name = 'friends/search_results.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query == '':
            queryset = []
        else:
            queryset = Author.objects.filter(
                Q(user__username__icontains=query) |
                Q(displayName__icontains=query),
            )
        
        return queryset
    
    def post(self, request, *args, **kwargs):
        author_id = request.user.author.id
        current_author = Author.objects.get(id=author_id)
        requested_id = request.POST['object_id']
        
        if requested_id == author_id:
            messages.warning(request, 'You cannot be friend with yourself')
            return redirect('author_manager:friends', author_id)
        try: 
            requested_author = get_object_or_404(Author, id=requested_id)
            
            if requested_author in current_author.followings.all():
                messages.warning(request, 'You already followed this author.')
                return redirect('author_manager:friends', author_id)

            friend_request, created = FriendRequest.objects.get_or_create(actor=current_author, object=requested_author)

            if created: 
                inbox = Inbox.objects.get(author=requested_author)
                inbox.follows.add(friend_request)
                messages.success(request, 'Your friend request has been sent.')
                return redirect('author_manager:friends', author_id)

            else:
                messages.warning(request, 'You already sent a friend request to this author.')
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
        # follow request
        inbox = Inbox.objects.get(author=current_author)
        return render(request, 'inbox/inbox.html', {'follows' : inbox.follows.all(), 'posts': inbox.posts.all()})
    
    if request.method == "POST":
        # Accept follow request -> follow back-> true friends
        if request.POST['type'] == 'befriend':
            requesting_author = Author.objects.get(id=request.POST['actor_id'])
            current_author.followers.add(requesting_author)
            requesting_author.followings.add(current_author)
           
            #delete the friend request:
            try:
                follow = FriendRequest.objects.get(actor=requesting_author, object=current_author)
                follow.delete()
            except:
                pass
            messages.success(request, 'Success to accept friend request.')
            return redirect('author_manager:inbox', author_id)



@login_required
def profile_edit(request, id):
    
    author = Author.objects.get(id=id)
    current_user = Author.objects.get(user=request.user)
    if current_user.id != id:
            error = "401 Unauthorized"
            return render(request, 'author_profile/edit_profile.html', {'error': error})
    if request.method == "GET":
        form = EditProfileForm(instance=author)
        return render(request, 'author_profile/edit_profile.html', {'form':form})
        
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
def get_profile(request, id):
    profile = Author.objects.get(id=id)
    return render(request, 'author_profile/profile.html', {'profile': profile})

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

    def get(self, request, id):
        """
        Handling GET request. Showing the author's profile.
        Returns:
            - If successful:
                Status 200 and the author's basic information.
        """
        profile = Author.objects.get(id=id)
        serializer = ProfileSerializer(profile, remove_fields=['user'] )
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


def format_timestamp(timestamp):
    '''
    Helper function to beautify github timestamp based on system's locale and language settings
    Params: timestamp - github timestamp in ISO 8601 format
    Return: beautified Python date object
    '''
    date = datetime.datetime.strptime(str(timestamp), "%Y-%m-%dT%H:%M:%SZ")
    date = date.strftime('%c')
    return date

@login_required
def github_events(request):
    '''
    The function handles get request and fetches all github public activities with given github username.
    Send request to github developer API.
    Handles event of types: WatchEvent, CreateEvent, DeleteEvent, ForkEvent, 
        PushEvent, PullRequestEvent, IssuesEvent.
    '''
    current_author = request.user.author
    if request.method =='GET':
        try:
            github_username = current_author.github  # get current author github's username

            # github API doc: https://docs.github.com/en/rest/reference/activity#events
            github_url = f"https://api.github.com/users/{github_username}/events/public"
            response = requests.get(github_url)
            # attempt validating if github username exists
            if response.status_code == 404:
                error = "404 User Not Found"
                return render(request, 'author_manager/github.html', {'error': error}, status=404)
            
            # process data to customized json response   
            data = response.json()  

            events = []
            for item in data:
                event = {}
                event["timestamp"] = str(format_timestamp(item["created_at"]))

                repo = item["repo"]["name"]
                event["url"] = item["repo"]["url"].replace('api.', '').replace('repos/', '')
                payload = item["payload"]

                if item["type"] == "WatchEvent":
                    event["type"] = "Watch"
                    event["message"] = f"{github_username} starred {repo}" 
                    events.append(event)

                if item["type"] == "CreateEvent":
                    event["type"] = "Create"
                    ref_type = payload["ref_type"]
                    ref = payload["ref"]
                    event["message"] =f"Created new {ref_type} {ref} within {repo}"
                    events.append(event)
                
                if item["type"] == "DeleteEvent":
                    event["type"] = "Delete"
                    ref_type = payload["ref_type"]
                    ref = payload["ref"]
                    event["message"] =f"Deleted {ref_type} {ref} within {repo}"
                    events.append(event)

                if item["type"] == "ForkEvent":
                    # username forked repo from forkee
                    event["type"] = "Fork"
                    forkee = payload["forkee"]["full_name"]
                    event["message"] = f"{github_username} forked {repo} from {forkee}"
                    events.append(event)
            
                if item["type"] == "PushEvent":
                    event["type"] = "Push"
                    head = payload["head"]
                    event["url"] = f"https://github.com/{repo}/commit/{head}"
                    event["message"] = f"{github_username} pushed to {repo}"
                    events.append(event)

                if item["type"] == "PullRequestEvent":
                    event["type"] = "PullRequest"
                    payload = payload["pull_request"]
                    number = payload["number"]
                    title = payload["title"]    
                    event["url"] = payload["html_url"]
                    event["message"] = f"Pull request opened: #{number} {title} in {repo}"
                    events.append(event)

                if item["type"] == "IssueEvent":
                    event["type"] = "Issue"
                    payload = payload["issue"]
                    number = payload["number"]
                    title = payload["title"]    
                    event["url"] = payload["html_url"]
                    event["message"] = f"Issue opened: #{number} {title} in {repo}"
                    events.append(event)

            return render(request, 'author_manager/github.html', {'events': events})
        
        except Exception as e:
            return render(request, 'author_manager/github.html')


class FriendsAPI(APIView):
    """
    An API endpoint allows viewing all the followers and followings of the requested author
    ...
    Methods:
        GET:
            Retrieve a list of followers and a list of followings of an author
    """
    
    def get(self, request, id):
        try:
            author = Author.objects.get(id=id)
        except:
            return Response({'detail': 'Not Found!'}, status=status.HTTP_404_NOT_FOUND)

        followers = author.followers.all()
        followings = author.followings.all()
        followers_serializer = ProfileSerializer(followers, remove_fields=['user'], many=True)
        followings_serializer = ProfileSerializer(followings, remove_fields=['user'], many=True)
        return Response({'type': 'friends', 'followers': followers_serializer.data, 'followings': followings_serializer.data}, status=status.HTTP_200_OK)


class FriendRequestsAPI(APIView):
    """
    An API endpoint allows viewing all the friend requests
    ...
    Methods:
        GET:
            Retrieve a list of friend requests 
    """
    
    def get(self, request):
        friendrequests = FriendRequest.objects.all()
        serializer = FriendRequestSerializer(friendrequests, many=True)
        response = {
            'type':  "follows",
            'items': serializer.data
        }
        return Response(response, status=status.HTTP_200_OK)