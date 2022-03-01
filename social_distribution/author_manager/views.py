from email.errors import MessageError
from django.contrib import messages
from django.shortcuts import redirect, render
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
    current_author = Author.objects.get(id=author_id)
    if request.method == "GET":
        followers = current_author.followers.all()
        followings = current_author.followings.all()
        friends = followings & followers
        # print(followers)
        # print(followings)
        # print(friends)
        return render(request, 'friends/friends.html', {'followings': followings, 'followers': followers, 'friends': friends})
    
    if request.method == "POST":
        requested_id = request.POST['object_id']
        if request.POST['type'] == 'send_friend_request':
            # print(1) 
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
                    # For simplicity, if userA request follow userB -> userA follows userB
                    # current_author.followings.add(requested_author)
                    # requested_author.followers.add(current_author)
                    messages.success(request, 'Your friend request has been sent.')
                    return redirect('author_manager:friends', author_id)

                else:
                    messages.warning(request, 'You already sent a friend request to this author.')
                    return redirect('author_manager:friends', author_id)
                
            except Author.DoesNotExist:
                messages.warning(request, 'Sorry, we could not find this author.')
                return redirect('author_manager:friends', author_id)

        # unfriend
        else:
            try:
                requested_author = get_object_or_404(Author, id=requested_id)
                current_author.followings.remove(requested_author)
                requested_author.followers.remove(current_author)

                mess = 'Your are now unfriend with ' + requested_author.displayName
                messages.success(request, mess)
                return redirect('author_manager:friends', author_id)
            except:
                return redirect('author_manager:friends', author_id)

    # actor = Author.objects.get(id=author_id)
    # followers = FollowerList.objects.get(author=actor)

    # if request.user.author != actor:
    #         return redirect('author_manager:login')

    # if request.method == "GET":
    #     # By definition friends = followers 
    #     return render(request, 'friends/friends.html', {'friends': followers.items.all()})

    # if request.method == "POST":
    #     object_id = request.POST['object_id']

    #     # send friend request
    #     if request.POST['type'] == 'send_friend_request':

    #         if object_id == author_id:
    #             messages.warning(request, 'You cannot be friend with yourself')
    #             return redirect('author_manager:friends', author_id)

    #         try:
    #             object = Author.objects.get(id=object_id)
    #             object_followers = FollowerList.objects.get(author=object)

    #             if object_followers.has_follower(actor):
    #                 messages.warning(request, 'You already followed this author.')
    #                 return redirect('author_manager:friends', author_id) 

    #             try:
    #                 friend_request = FriendRequest.objects.get(actor=actor, object=object)
    #                 messages.warning(request, 'You already sent a friend request to this author.')
    #                 return redirect('author_manager:friends', author_id)
                
    #             except FriendRequest.DoesNotExist:
    #                 friend_request = FriendRequest(actor=actor, object=object)
    #                 friend_request.save()

    #                 inbox = Inbox.objects.get(author=object)
    #                 inbox.follows.add(friend_request)

    #                 messages.success(request, 'Your friend request has been sent.')
    #                 return redirect('author_manager:friends', author_id)

    #         except Author.DoesNotExist:
    #             messages.warning(request, 'Sorry, we could not find this author.')
    #             return redirect('author_manager:friends', author_id)
        
    #     # unfriend
    #     else:
    #         try:
    #             object = Author.objects.get(id=object_id)
    #             followers.items.remove(object)

    #             mess = 'Your are now unfriend with ' + object.displayName
    #             messages.success(request, mess)
    #             return redirect('author_manager:friends', author_id)
    #         except:
    #             pass




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

            # object_followers = FollowerList.objects.get(author=current_author)
            
            # try:
            #     actor = Author.objects.get(id=request.POST['actor_id'])
            # except Author.DoesNotExist:
            #     messages.warning(request, 'Sorry, we could not find this author.')
            
            # if actor:
            #     # add actor to the follwer list of current author:
            #     object_followers.items.add(actor)

            #     #delete the friend request:
            #     try:
            #         follow = FriendRequest.objects.get(actor=actor, object=current_author)
            #         follow.delete()
            #     except:
            #         pass
            
            # # messages.success(request, 'Success to accept friend request.')
            # return redirect('author_manager:inbox', author_id)

    

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
            print(github_username)
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

                


                    

