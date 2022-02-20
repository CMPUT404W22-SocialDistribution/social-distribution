from django.shortcuts import render
from rest_framework import generics, authentication, permissions

from .serializers import PostSerializer
from .models import Post
from author_manager.models import *
from rest_framework.response import Response

class PostsAPI(generics.GenericAPIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer
    def get(self,request, author_id):
        author = Author.objects.get(id=author_id)
        posts = author.posts.filter(unlisted=False).all()
        current_author = Author.objects.get(user=request.user)
        if current_author.id != author.id:
            posts = posts.filter(visibility='public')

        serializer = PostSerializer(posts, many=True)
        content = {
            'current author': current_author.displayName,
            'author': author.displayName,
            'posts': serializer.data
        }
        return Response(content, 200)
        

        
    def post(self, request, author_id):
        author = Author.objects.get(id=author_id)
        if request.user.author != author:
            return Response({'detail': 'Access denied'}, 401)
        
        post = Post.objects.create(author=author)
        serializer = PostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            content = {
                'status': 1,
                'post': serializer.data
            }
            return Response(content, 200)
        return Response(serializer.errors, 400)

#class PostDetailAPi