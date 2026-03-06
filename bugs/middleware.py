from django.shortcuts import redirect,render
from django.urls import reverse
from django.utils.cache import add_never_cache_headers

from django.shortcuts import redirect
from django.conf import settings



from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch

# class LoginRequiredMiddleware:

#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):

#         #  Allowed URLs — resolved inside __call__ not __init__
#         allowed_urls = [
#             reverse('login'),
#         ]

        

        # #  Allow admin
        # if request.path.startswith('/admin/'):
        #     return self.get_response(request)

        # #  Allow static & media
        # if request.path.startswith(('/static/', '/media/')):
        #     return self.get_response(request)

        # # Allow allowed URLs
        # if request.path in allowed_urls:
        #     return self.get_response(request)

        
        # #  Redirect if not logged in
        # if not request.user.is_authenticated:
        #     return redirect('/login')


        
        # return self.get_response(request)



# class LoginRequiredMiddleware:

#     def __init__(self, get_response):
#         self.get_response = get_response  

#     def __call__(self, request):
#         response = self.get_response(request)
#         add_never_cache_headers(response)
#         return response



# def auth(view_function):
#     def wrapped_view(request,*args,**kwargs):
#         if request.user.is_authenticated == False:
#             return redirect('login')
#         return view_function(request,*args,**kwargs)
#     return wrapped_view    







class LoginRequiredMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

        self.exempt_urls = [
            getattr(settings, 'LOGIN_URL', '/'),
            '/logout/',
        ]

    def __call__(self, request):

        # allow login/logout URLs
        is_exempt = any(request.path == url for url in self.exempt_urls)

        # allow admin URLs
        is_admin = request.path.startswith('/admin/')

        if not request.user.is_authenticated and not (is_exempt or is_admin):
            return redirect(settings.LOGIN_URL)

        response = self.get_response(request)

        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response
