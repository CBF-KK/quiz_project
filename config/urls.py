from django.contrib import admin
from django.urls import path
from quiz import views

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_user, name="login"),
    path("quiz/", views.home, name="home"),
    path("history/", views.history, name="history"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_user, name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)