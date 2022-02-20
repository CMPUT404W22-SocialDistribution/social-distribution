from django.shortcuts import render
from rest_framework import generics, authentication, permissions

from social_distribution.posts.serializers import PostSerializer
from.models import Post
from author_manager.models import *
from rest_framework.response import Response

class PostsAPI(generics.GenericAPIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get(self,request, author_id):
        author = Author.objects.get(id=author_id)
        posts = author.posts.all()
        current_user = request.user
        if current_user.id != author_id:
            posts.filter(unlisted=False)
        serializer = self.get_serializer(posts, many=True)
        if serializer.is_valid():
            content = {
                'author': author,
                'posts': serializer.data
            }
            return Response(content, 200)
        return Response(serializer.errors, 400)

        
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