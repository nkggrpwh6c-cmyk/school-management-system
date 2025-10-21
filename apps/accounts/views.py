from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User, UserProfile
from .forms import CustomUserCreationForm, UserUpdateForm, UserProfileForm


class CustomLoginView(LoginView):
    """
    Custom login view with role-based redirection
    """
    template_name = 'accounts/login.html'
    form_class = AuthenticationForm
    
    def form_valid(self, form):
        """Override form_valid to add debugging"""
        print(f"Login attempt for user: {form.cleaned_data.get('username')}")
        response = super().form_valid(form)
        print(f"Login successful, redirecting to: {self.get_success_url()}")
        return response
    
    def get_success_url(self):
        user = self.request.user
        # Check role first, then permissions
        if user.is_student():
            return '/students/'
        elif user.is_teacher():
            return '/teachers/'
        elif user.is_parent():
            return '/parents/'
        elif user.username == 'security_admin' or (user.is_superuser and user.username == 'admin'):
            # Redirect admin and security_admin to admin dashboard
            return '/accounts/admin-dashboard/'
        elif user.is_admin() or user.is_staff:
            # Redirect registrar to registrar dashboard
            return '/registrar/'
        else:
            return '/'


class SignUpView(CreateView):
    """
    User registration view
    """
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! Please login.')
        return response


@login_required
def profile_view(request):
    """
    User profile view
    """
    user = request.user
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def dashboard_view(request):
    """
    Role-based dashboard redirect
    """
    user = request.user
    if user.is_student():
        return redirect('students:dashboard')
    elif user.is_teacher():
        return redirect('teachers:dashboard')
    elif user.is_parent():
        return redirect('parents:dashboard')
    elif user.is_admin() or user.is_staff:
        return redirect('/registrar/')
    else:
        return redirect('accounts:profile')


def logout_view(request):
    """
    Custom logout view
    """
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')
