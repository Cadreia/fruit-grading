from django.conf.urls import url
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from main.views import FileView
from . import views
from .views import GeneratePdf

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
    url(r'^grade$', views.success),
    url(r'^results$', views.results),
    url(r'^dashboard$', views.dashboard),
    url(r'^login$', views.index2),
    url(r'^logout', views.logout_view),
    #url(r'^detectWithCamera', views.detectWithCamera),
    #url(r'^upload', FileView.as_view(), name='file-upload'),
    url(r'^pdf/$', GeneratePdf.as_view()),


    path('update_company/<id>', views.updateCompany, name='updateCompany'),
    path('delete_company/<id>', views.deleteCompany, name='deleteCompany'),
    path('view_branches/<companyId>', views.viewBranches, name='viewBranches'),
    path('add_branch/<companyId>', views.addBranch, name='addBranch'),
    path('save_branch/<companyId>', views.saveBranch, name='saveBranch'),
    path('companies/<companyId>/branches/<branchId>', views.updateBranch, name='updateBranch'),
    path('companies/<companyId>/branches/<branchId>/delete', views.deleteBranch, name='deleteBranch'),
    path('companies/<companyId>/branches/<branchId>/view_branch', views.viewBranch, name='viewBranch'),
    path('view_fruits', views.viewFruits, name='viewFruits'),
    path('add_fruit', views.addFruit, name='addFruit'),
    path('save_fruit', views.saveFruit, name='saveFruit'),
    path('update_fruit/<fruitId>', views.updateFruit, name='updateFruit'),
    path('delete_fruit/<fruitId>', views.deleteFruit, name='deleteFruit'),
    path('check_fruit/branch/<branchId>/fruit/<fruitId>', views.checkFruit, name='checkFruit'),
    path('companies/<companyId>/branches/<branchId>/view_report', views.viewReport, name='viewReport'),
    path('gotoCamResults/branch/<branchId>/fruit/<fruitId>', views.gotoCamResults, name='gotoCamResults'),
    path('detectWithCamera', views.detectWithCamera, name='detectWithCamera'),
    path('startCamGrading', views.startCamGrading, name='startCamGrading'),

    url(r'^reports', views.viewReports),

    #url(r'^accounts/', include('allauth.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
