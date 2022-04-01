from app import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', views.index, name="index"),
    path('admin/', admin.site.urls),
    path('administrator/', views.admin, name="administrator"),
    path('accounts/register/',
         views.CustomRegistrationView.as_view(success_url='/'),
         name='django_registration_register'),
    path('accounts/', include('django_registration.backends.one_step.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

    #insurance staff
    path('insurance_staff/',views.viewClaim,name='insurance_staff'),
#     path('insurance_staff_review/',views.claimDisb,name='claimDisb'),
    #path('approveClaim/<str:pk>',views.approveClaim,name='approveClaim'),
    #path('denyClaim/<str:pk>',views.denyClaim,name='denyClaim'),
    path('authorizeFund/',views.authorizeFund,name= 'authorizeFund'),

    #hospital staff
    path('hospital_staff_appointments/', views.hospital_appointment,
         name='hospital_staff_appointments'),
    path('hospital_staff_create_payment/', views.hospital_transaction, name='hospital_staff_create_payment'),
    path('hospital_search_patients/', views.hospital_search,
         name='hospital_search_patients'),
    path('hospital_update_patients/',views.hospital_update_patients,name= 'hospital_update_patients'),
    path('hospital_appointment_approve/<str:ID>',views.hospital_appointment_approve,name='hospital_appointment_approve'),
    path('hospital_appointment_reject/<str:ID>',views.hospital_appointment_reject,name='hospital_appointment_reject'),
#     path('hospital_search_patients_filter/',views.hospital_search_patients_filter,name= 'hospital_search_patients_filter'),
    path('hospital_patient_details/<str:pID>',views.hospital_patient_details,name= 'hospital_patient_details'),
    
    # Patient urls
    path("patient", views.patient, name='patient'),
    path('bot', views.get_bot_response),
    path('patient_details/<str:patientID>', views.patient_details, name='patient_details'),
    path('patient_details/update_patient_details/<str:patientID>', views.update_patient_record, name='update_patient_details'),
    path("patient_appointment", views.patient_appointment_view, name="patient_appointment"),
    path('patient_book_appointment/<str:patientID>', views.patient_book_appointment_view,name='patient_book_appointment'),
#     path('patient-view-appointment', views.patient_view_appointment_view, name='patient-view-appointment'),
    path('patient_diagnosis/<str:patientID>', views.patient_diagnosis_details, name='patient_diagnosis'),
    path('patient_prescription/<str:patientID>', views.patient_diagnosis_details, name='patient_prescription'),

    path("patient_labtest/<str:patientID>", views.patient_labtest_view, name="patient_labtest"),
    path("patient_labtest/request_labtest/<str:patientID>", views.request_test, name="request_labtest"),
    path("patient_labtest/patient_view_lab_report/<str:patientID>", views.view_lab_report, name="patient_view_lab_report"),
         
  
# doctor urls
    path('doctor/', views.doctor, name='doctor'),
    path('doctor_view_appointment_view/', views.doctor_view_appointment_view, name='doctor_appointment'),

    # Doctor URLs
    path('doctor/', views.doctor, name='doctor'),
    path('doctor_view_appointment_view/',
         views.doctor_view_appointment_view, name='doctor_appointment'),
    path('doctor_book_appointment/', views.doctor_book_appointment,
         name='doctor_book_appointment'),
    path('doctor_view_patientlist/', views.doctor_view_patientlist,
         name='doctor_view_patientlist'),
    path('doctor_appointmentID_search_view/', views.doctor_appointmentID_search_view,
         name='doctor_appointmentID_search_view'),
    path('doctor_search/', views.doctor_search_view,
         name='doctor_search'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
