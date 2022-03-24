from email import header
from enum import Flag
from os import stat
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.views.generic import ListView
from rest_framework import authentication, permissions
from rest_framework import status
from rest_framework import generics, authentication, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser
from node.authentication import basic_authentication
import requests
import datetime
from node.models import Node
from posts.models import Comment

from rest_framework.response import Response
from rest_framework.views import APIView

import posts.serializers
from posts.models import Post
from posts.serializers import CommentSerializer, PostSerializer
from .forms import SignUpForm, EditProfileForm
from .models import *
from .serializers import *
import json


from node.authentication import basic_authentication

HEADERS = {'Referer': 'http://squawker-cmput404.herokuapp.com/', 'Mode': 'no-cors'}
# URL = 'http://squawker-cmput404.herokuapp.com/'
T08_USERNAME = 'squawker'
T08_PASS = 'sQu@k3r'
CLONE_USERNAME = 'squawker-dev'
CLONE_PASS = 'cmput404'

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
                user.author.host = 'http' + '://' + request.META['HTTP_HOST'] + '/'
                user.author.url = user.author.host + 'authors/' + str(user.author.id)
                user.author.save()
            else:
                user.author.host = 'http' + '://' + request.get_host() + '/'
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
        return render(request, 'friends/friends.html',
                      {'followings': followings, 'followers': followers, 'friends': friends})

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
            queryset = []
            query_local_authors = Author.objects.filter( 
                                    Q(user__username__icontains=query)|Q(displayName__icontains=query))

            for author in query_local_authors:
                queryset.append({'id': author.id, 'username': author.user.username, 
                                 'profileImage': author.profileImage, 'displayName': author.displayName, 'url': author.url})
            
            for node in Node.objects.all():
                # # Team 8
                # if node.url == 'http://project-socialdistribution.herokuapp.com/' :
                #     authors_url = node.url + 'api/authors/'
                # # Clone
                # elif  node.url == 'https://squawker-dev.herokuapp.com/':
                #     authors_url = node.url + 'api/authors/'
                authors_url = node.url + 'api/authors/'
                response = requests.get(authors_url, headers=HEADERS, auth=(node.outgoing_username, node.outgoing_password))
                if response.status_code == 200:
                    authors = response.json()['items']
                    for author in authors:
                        if query in author["displayName"]:
                            queryset.append(
                                {'id': author['id'], 'username': 'remote author', 
                                    'profileImage': 'profile_picture.png', 'displayName': author['displayName'], 'url': author['url']})

        return queryset

    def post(self, request, *args, **kwargs):
        author_id = request.user.author.id
        current_author = Author.objects.get(id=author_id)
        requested_id = request.POST['object_id']

        if requested_id == author_id:
            messages.warning(request, 'You cannot be friend with yourself')
            return redirect('author_manager:friends', author_id)
        try:
            if 'http' in requested_id:
                #T08
                if 'project-socialdistribution' in requested_id:
                    service = 't08' 
                    requested_id = requested_id.split('/')[-2]
                    author_url = 'http://project-socialdistribution.herokuapp.com/api/authors/' + requested_id + "/"
                    follow_url = author_url + 'followers/' + author_id + '/'
                    inbox_url = author_url +'inbox/'
                    outgoing_username = T08_USERNAME
                    outgoing_password = T08_PASS
                #Clone
                else:
                    service = 'clone'
                    requested_id = requested_id.split('/')[-1]
                    author_url = 'https://squawker-dev.herokuapp.com/api/authors/' + requested_id
                    follow_url = author_url + '/followers/' + author_id
                    inbox_url = author_url + '/inbox'
                    outgoing_username = CLONE_USERNAME
                    outgoing_password = CLONE_PASS

                response = requests.get(author_url, headers=HEADERS, auth=(outgoing_username, outgoing_password))

                if response.status_code == 200:
                    object = response.json()
                else: # cannot found the remote author
                    messages.warning(request, 'Sorry, we could not find this author.')
                    return redirect('author_manager:friends', author_id)

                # check if already follow
                response = requests.get(follow_url, headers=HEADERS, auth=(outgoing_username, outgoing_password))
        
                # if not follow yet
                if response.status_code == 404 or response.json()["ok"] == []:
                    actor = {
                        "type": "author",
                        "id": current_author.url,
                        "url": current_author.url,
                        "host": current_author.host,
                        "displayName": current_author.displayName,
                        "github": current_author.github,
                        "profileImage": current_author.profileImage
                    }

                    friend_request = {
                        "type": "follow",
                        "summary": "follow request",
                        "actor": actor,
                        "object": object
                    }

                    if service == "clone":
                        friend_request = {"item" : friend_request}

                    headers = HEADERS + {"Content-Type": "application/json"}
                    response =  requests.post(inbox_url, json=json.dumps(friend_request), headers=headers, auth=(outgoing_username, outgoing_password))
                    print(headers)
                    print(response.json())
                    print(response.status_code)

                    if response.status_code == 200:
                        messages.success(request, 'Your friend request has been sent.')
                    elif response.status_code == 204:
                        messages.success(request, 'You already followed this author.')
                    else:
                        messages.warning(request, 'Could not send the friend request to this author !')

                    return redirect('author_manager:friends', author_id)

            else:
                requested_author = get_object_or_404(Author, id=requested_id)

                if requested_author in current_author.followings.all():
                    messages.warning(request, 'You already followed this author.')
                    return redirect('author_manager:friends', author_id)

                actor = ProfileSerializer(current_author, remove_fields=['user']).data
                object = ProfileSerializer(requested_author, remove_fields=['user']).data
                friend_request = {"type": "follow", "actor": actor, "object": object}

                inbox = Inbox.objects.get(author=requested_author)

                if friend_request in inbox.follows:
                    messages.warning(request, 'You already sent a friend request to this author.')
                    return redirect('author_manager:friends', author_id)

                inbox.follows.append(friend_request)
                inbox.save()
                messages.success(request, 'Your friend request has been sent.')
                return redirect('author_manager:friends', author_id)


        except Author.DoesNotExist:
            messages.warning(request, 'Sorry, we could not find this author.')
            return redirect('author_manager:friends', author_id)


@login_required
def inbox_view(request, id):
    current_author = Author.objects.get(id=id)

    if request.user.author != current_author:
        return redirect('author_manager:login')

    if request.method == "GET":
        # follow request
        inbox = Inbox.objects.get(author=current_author)
        return render(request, 'inbox/inbox.html', {
            'follows': inbox.follows,
            'posts': inbox.posts.all(),
            'comments': inbox.comments.all(),
            'likes': inbox.likes.all().order_by('-id')
        })

    if request.method == "POST":
        # Accept follow request -> follow back-> true friends
        if request.POST['type'] == 'befriend':
            requesting_author = Author.objects.get(id=request.POST['actor_id'])
            current_author.followers.add(requesting_author)
            requesting_author.followings.add(current_author)

            # delete the friend request:
            try:
                follow = FriendRequest.objects.get(actor=requesting_author, object=current_author)
                follow.delete()
            except:
                pass
            messages.success(request, 'Success to accept friend request.')
            return redirect('author_manager:inbox', id)

        if request.POST['type'] == 'comment':
            comment = request.POST['comment']
            inbox_comment = Comment.objects.get(id=comment)
            current_author.inbox.comments.remove(inbox_comment)
            post_author = request.POST['post_author']
            post =  request.POST['post']
            return redirect('posts:post_detail', post_author, post)

@login_required
def profile_edit(request, id):
    author = Author.objects.get(id=id)
    current_user = Author.objects.get(user=request.user)
    if current_user.id != id:
        error = "401 Unauthorized"
        return render(request, 'author_profile/edit_profile.html', {'error': error})
    if request.method == "GET":
        form = EditProfileForm(instance=author)
        return render(request, 'author_profile/edit_profile.html', {'form': form})

    elif request.method == "POST":
        updated_request = request.POST.copy()
        form = EditProfileForm(updated_request, instance=author)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('author_manager:profile', id)
        else:
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
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []

    def get(self, request, id):
        """
        Handling GET request. Showing the author's profile.
        Returns:
            - If successful:
                Status 200 and the author's basic information.
        """
        local, remote = basic_authentication(request)
        if not local and not remote:

            return Response({'detail': 'Access denied'}, status=status.HTTP_401_UNAUTHORIZED)


        profile = get_object_or_404(Author, id=id)
        if local:
            serializer = ProfileSerializer(profile, remove_fields=['user'])
        else:
            serializer = RemoteProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, id):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get object we want to update
        update_user = get_object_or_404(Author, id=id)  # make sure author in url exists
        current_user = Author.objects.get(user=request.user)

        if (current_user.id == id):  # current user and user needs to be updated matched
            if local:
                serializer = ProfileSerializer(update_user, data=request.data, partial=True, remove_fields=['user'])
            else:
                serializer = RemoteProfileSerializer(update_user, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                response = {
                    "status": 1,
                    "message": serializer.errors,
                }
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Current user is not authorized to do this operation'},
                        status=status.HTTP_401_UNAUTHORIZED)


class GetAllAuthors(APIView):
    """
    An API endpoint allows viewing all author's profile
    ...
    Methods:
        GET:
            Retrieve all author's profiles
    """
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []

    def get(self, request):
        """
        Handling GET request. Showing all author's profiles.
        Returns:
            - If successful:
                Status 200 and the author's basic information.
        """
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, status=status.HTTP_401_UNAUTHORIZED)


        authors = Author.objects.all()
        if local:
            serializer = ProfileSerializer(authors, many=True, remove_fields=['user'])
        else:
            serializer = RemoteProfileSerializer(authors, many=True)

        response = {
            'type': "authors",
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
    if request.method == 'GET':
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
                    event["message"] = f"Created new {ref_type} {ref} within {repo}"
                    events.append(event)

                if item["type"] == "DeleteEvent":
                    event["type"] = "Delete"
                    ref_type = payload["ref_type"]
                    ref = payload["ref"]
                    event["message"] = f"Deleted {ref_type} {ref} within {repo}"
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
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []

    def get(self, request, id):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            author = Author.objects.get(id=id)
        except:
            return Response({'detail': 'Not Found!'}, status=status.HTTP_404_NOT_FOUND)
        
        followers = author.followers.all()
        if local:
            followers_serializer = ProfileSerializer(followers, remove_fields=['user'], many=True)
        else: #remote
            followers_serializer = RemoteProfileSerializer(followers, many=True)

        # followings_serializer = ProfileSerializer(followings, remove_fields=['user'], many=True)
        return Response(
            {'type': 'followers', 'items': followers_serializer.data},
            status=status.HTTP_200_OK)


class FriendDetailAPI(APIView):
    """
        To do: remote and put
    """
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []
    serializer_class = ProfileSerializer

    def get(self, request, author_id, follower_id):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            author = Author.objects.get(id=author_id)
            follower = Author.objects.get(id=follower_id)
            
            if follower in author.followers.all():
                if local:
                    followers_serializer = ProfileSerializer(follower, remove_fields=['user'], many=False)
                else:
                    followers_serializer = RemoteProfileSerializer(follower, many=False)

                return Response(followers_serializer.data, status=status.HTTP_200_OK)

            return Response({'detail': 'Not Found!'}, status=status.HTTP_404_NOT_FOUND)

        except:
            return Response({'detail': 'Not Found!'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, author_id, follower_id):
        try:
            author = Author.objects.get(id=author_id)
            follower = Author.objects.get(id=follower_id)
            
            if follower in author.followers.all():
                author.followers.remove(follower)
                return Response({'message': 'Success to unfriend/unfollow'}, status=status.HTTP_200_OK)

            return Response({'detail': 'Not Found!'}, status=status.HTTP_404_NOT_FOUND)

        except:
            return Response({'detail': 'Not Found!'}, status=status.HTTP_404_NOT_FOUND)

        

class FriendRequestsAPI(APIView):
    """
    An API endpoint allows viewing all the friend requests and create a friend request
    ...
    Methods:
        GET:
            Retrieve a list of friend requests 
        POST:
            Create a friend requests
    """

    def get(self, request):
        friendrequests = FriendRequest.objects.all()
        serializer = FriendRequestSerializer(friendrequests, many=True)
        response = {
            'type': "follows",
            'items': serializer.data
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FriendRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthorLikedAPI(APIView):
    authentication_classes = [authentication.BasicAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = posts.serializers.LikeSerializer

    def get(self, request, author_id):
        # The requester should only be able to view likes of public posts or non-public posts that are visible to them
        likes = Like.objects.filter(author__exact=author_id, post__visibility__exact=Post.VisibilityType.PUBLIC) | \
                Like.objects.filter(author__exact=author_id, post__visibleTo__contains=request.user.author.id)
        if not likes:
            raise Http404

        serializer = self.serializer_class(likes, many=True)
        return Response(
            data={
                'type': 'liked',
                'size': len(serializer.data),
                'items': serializer.data
            },
            status=status.HTTP_200_OK)

class CustomPagination(PageNumberPagination):
    '''
    Helper Pagination class to paginate Inbox API by the query options: page, size 
    '''
    page_size = 1000
    page_size_query_param = 'size'
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(
        {
            'type': 'inbox',
            'author': data['url'],
            'items': data['items']
        },  
        status=status.HTTP_200_OK
        )

class InboxAPI(generics.GenericAPIView):
    """
    An API endpoint allows viewing the inbox of the author id, send a post to the inbox and clear the inbox.
    The post here can be type: post, follow, like, comment
    Require authorization.
    ...
    Methods:
        GET:
            Retrieve all the posts that are sent to the author id
            Support pagination 
        POST:
            Send/Add post to the author's inbox according to its type:
                - type is “post” then add that post to the posts list of the inbox
                - type is “follow” then add that follow/friend request to the follows list of the inbox: request is waiting for approve
                - type is “like” then add that like to the likes list of the inbox
                - type is “comment” then add that comment to the comments list of the inbox
        DELETE:
            clear the inbox: there is no posts/items in the inbox
    """

    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []
    pagination_class = CustomPagination
    serializer_class = InboxSerializer
    # parser_classes = [JSONParser]

    def get(self, request, id):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            author = Author.objects.get(id=id)
            inbox = Inbox.objects.get(author=author)
        except:
            return Response({'detail': 'Not Found!'}, status=status.HTTP_404_NOT_FOUND)

        post_serializer = PostSerializer(inbox.posts, many=True)
        comment_serializer = CommentSerializer(inbox.comments, many=True)
        like_serializer = LikeSerializer(inbox.likes, many=True)

        items = inbox.follows + post_serializer.data + comment_serializer.data + like_serializer.data

        # Pagination:
        part_items = self.paginator.paginate_queryset(items, request)
        
        return self.paginator.get_paginated_response({'items': part_items, 'url': author.url})

    @staticmethod
    def _get_already_liked(author_id, post_id, comment_id):
        if comment_id:
            like_query_set = Like.objects.filter(author__id__exact=author_id,
                                                 post__id__exact=post_id,
                                                 comment__id__exact=comment_id)
        else:
            like_query_set = Like.objects.filter(author__id__exact=author_id,
                                                 post__id__exact=post_id,
                                                 comment__id__isnull=True)

        if like_query_set:
            return like_query_set[0]
        return None

    def post(self, request, id):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            print(request.body)
            author = Author.objects.get(id=id)
            inbox = Inbox.objects.get(author=author)
            print(request.data)
            item = request.data['item']
            item_type = item['type']

            if item_type == 'like':
                like_serializer = LikeSerializer(data=item)
                if like_serializer.is_valid():
                    post = like_serializer.validated_data['post']

                    # Do not like the same object twice
                    comment = like_serializer.validated_data.get('comment', None)
                    like_author = like_serializer.validated_data['author']
                    if comment:
                        previous_like = self._get_already_liked(like_author.id, post.id, comment.id)
                    else:
                        previous_like = self._get_already_liked(like_author.id, post.id, None)
                    if previous_like:
                        return Response(LikeSerializer().to_representation(previous_like),
                                        status=status.HTTP_204_NO_CONTENT)

                    like_serializer.save()

                    # Except for self-likes, send like object to recipient's inbox
                    if id != like_author.id:
                        inbox.likes.add(like_serializer.instance.id)
                    return Response(posts.serializers.LikeSerializer().to_representation(like_serializer.instance),
                                    status=status.HTTP_200_OK)
                return Response(like_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if item_type == 'follow':
                # if author.url != item['object']['id'] or author.url == item['actor']['id']:
                #     return Response({'detail': 'Fail to send the item!'}, status=status.HTTP_400_BAD_REQUEST)
                if item in inbox.follows:
                    return Response({'message': 'Already sent follow/friend request'}, status=status.HTTP_204_NO_CONTENT)

                inbox.follows.append(item)
                inbox.save()
                return Response({'message': 'Success to send follow/friend request'}, status=status.HTTP_200_OK)
            
            item_id = item['id']

            if item_type == 'post':
                post = Post.objects.get(id=item_id)
                inbox.posts.add(post)
                return Response({'message': 'Success to send post'}, status=status.HTTP_200_OK)

            if item_type == 'comment':
                comment = Comment.objects.get(id=item_id)
                inbox.comments.add(comment)
                return Response({'message': 'Success to send comment'}, status=status.HTTP_200_OK)

            return Response({'detail': 'Fail to send the item!'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return Response({'detail': 'Fail to send the item!'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            author = Author.objects.get(id=id)
            inbox = Inbox.objects.get(author=author)

            inbox.follows = []
            inbox.posts.set([], clear=True)
            inbox.comments.set([], clear=True)
            inbox.likes.set([], clear=True)
            inbox.save()

            return Response({'message': 'Success to clean inbox'}, status=status.HTTP_200_OK)
        except:
            return Response({'detail': 'Fail to clear inbox!'}, status=status.HTTP_400_BAD_REQUEST)
        