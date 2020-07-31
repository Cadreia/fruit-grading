from django.conf.urls import url
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from main.views import FileView
from . import views

urlpatterns = [
    url(r'^$', views.home),
    url(r'^home', views.home),
    url(r'^register', views.showRegister),
    url(r'^signup', views.register),
    url(r'^login', views.index2),
    url(r'^add_user', views.addUser),
    url(r'^save_user', views.saveUser),
    url(r'^view_users', views.viewUsers),
    url(r'^add_company', views.addCompany),
    url(r'^save_company', views.saveCompany),
    url(r'^view_companies', views.viewCompanies),
    url(r'^add_branch', views.addBranch),
    url(r'^save_branch', views.saveBranch),
    url(r'^view_branches', views.viewBranches),
    url(r'^grade$', views.success),
    url(r'^results$', views.results),
    url(r'^dashboard$', views.dashboard),
    url(r'^gotoCamResults$', views.gotoCamResults),

    url(r'^login$', views.index2),
    url(r'^logout', views.logout_view),
    url(r'^checkFruit', views.checkFruit),
    #url(r'^detectWithCamera', views.detectWithCamera),
    #url(r'^upload', FileView.as_view(), name='file-upload'),

    path('detectWithCamera', views.detectWithCamera, name='detectWithCamera'),

    url(r'^reports', views.viewReports),

    #url(r'^accounts/', include('allauth.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
