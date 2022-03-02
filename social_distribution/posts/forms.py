from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django import forms

from .models import Post

# https://simpleisbetterthancomplex.com/tutorial/2018/11/28/advanced-form-rendering-with-django-crispy-forms.html

col12 = 'form-group col-md-12 mb-0'
col6 = 'form-group col-md-6 mb-0'
col4 = 'form-group col-md-4 mb-0'
col3 = 'form-group col-md-3 mb-0'
col2 = 'form-group col-md-2 mb-0'
col1 = 'form-group col-md-1 mb-0'


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = "__all__"
        widgets = {
            'categories': forms.Select(attrs={'rows': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('title', css_class=col12),
            ),
            Row(
                Column('source', css_class=col6),
                Column('origin', css_class=col6),
            ),
            Row(
                Column('description', css_class=col12),
            ),
            Row(
                Column('content_type', css_class=col4),
                Column('visibility', css_class=col4),
                Column('visibleTo', css_class=col4),
                # Column('categories', css_class=col4),
            ),
            Row(
                Column('categories', css_class=col12),
            ),
            Row(
                Column('content', css_class=col12),
            ),
            Row(
                Column('image', css_class=col12),
            ),
            Row(
                Column('unlisted', css_class=col12),
            ),
            Submit('submit', 'Submit')
        )
