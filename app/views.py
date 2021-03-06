from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django_otp import match_token
from django_otp.decorators import otp_required
from django_registration.backends.one_step.views import RegistrationView
from django_registration.forms import RegistrationForm

from app.decorators import check_view_permissions

from . import forms, models
from .BotMain import chatgui  # Botmain is chatbot directory
from .models import (Appointment, Diagnosis, Doctor, Insurance, Patient,
                     Payment, Test)
from .render import Render


@otp_required(login_url="account/two_factor/setup/")
@login_required(redirect_field_name="two_factor")
def index(request):
    print(request.user.groups)
    if request.user.groups.filter(name='patient').exists():
        return redirect('/patient')
    if request.user.groups.filter(name='doctor').exists():
        return redirect('/doctor')
    if request.user.groups.filter(name='hospital_staff').exists():
        return redirect('/hospital_staff_appointments')
    if request.user.groups.filter(name='lab_staff').exists():
        return redirect('/lab_staff')
    if request.user.groups.filter(name='insurance_staff').exists():
        return redirect('/insurance_staff')
    if request.user.groups.filter(name='admin').exists():
        return redirect('/admin')


class Register(RegistrationView):
    form_class = RegistrationForm
    success_url = None
    template_name = "django_registration/registration_form.html"

    def register(self, form):
        new_user = form.save()
        patient_group = Group.objects.get(name='patient')
        patient_group.user_set.add(new_user)
        obj = Patient()
        obj.patientID = new_user.username
        obj.save()


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("admin")
def admin(request):
    return render(request=request, template_name="administrator/index.html", context={'hello': "hello"})


''' Lab Staff View Starts Here'''
@login_required
@check_view_permissions("lab_staff")
def lab_test_search(request):
    # whatever user write in search box we get in query
    query = request.GET.get('search', False)
    patients = Patient.objects.all().filter(
        Q(patientID__icontains=query) | Q(name__icontains=query))
    arr = []
    for i in patients:
        obj = Test.objects.all().filter(patientID=i.patientID)
        for j in obj:
            if j.status == 'approved' or j.status == 'completed':
                dict = {
                    'patientID': j.patientID.patientID,
                    'testID': j.testID,
                    'date': j.date,
                    'type': j.type,
                    'result': j.result
                }
                arr.append(dict)
    return render(request, 'lab_staff/lab_tests.html', {'patients': arr})


@login_required
@check_view_permissions("lab_staff")
def updateTests(request, pk):
    d = Test.objects.get(testID=pk)
    EditReportForm = forms.EditReportForm(request.POST)

    if request.method == 'POST':
        d.result = EditReportForm.data['result']
        d.save()
        if EditReportForm.is_valid():
            print("Form is valid")
            d.save()

        d = Test.objects.get(testID=pk)
        return redirect('/lab_tests')

    mydict = {'EditReportForm': EditReportForm}
    return render(request, 'lab_staff/lab_tests_approved.html', context=mydict)


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("lab_staff")
def viewDiagnosis(request):
    obj = Test.objects.all().filter(status='requested')
    arr = []
    for i in obj:
        obj1 = Patient.objects.get(patientID=i.patientID.patientID)
        obj2 = Diagnosis.objects.get(diagnosisID=i.diagnosisID.diagnosisID)
        dict = {
            'PatientName': obj1.name,
            'Diagnosis': obj2.diagnosis,
            'diagnosisId': i.diagnosisID.diagnosisID,
            'Recommendations': obj2.test_recommendation,
            'testID': i.testID,
            'type' : i.type
        }
        arr.append(dict)
    return render(request, "lab_staff/lab_staff.html", {'requests': arr})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("lab_staff")
def denyTest(request, pk):
    obj = Test.objects.get(testID=pk)
    obj.status = 'denied'
    obj.save()
    return redirect('/lab_staff')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("lab_staff")
def approveTest(request, diagnosisID, pk):
    obj = Test.objects.get(testID=pk)
    obj.status = 'approved'
    obj.save()
    # update appointment table if test is approved
    diagnosisObj = Diagnosis.objects.get(diagnosisID = diagnosisID)
    print(diagnosisObj)
    appointmentObject = Appointment.objects.get(appointmentID = diagnosisObj.appointmentID.appointmentID)
    appointmentObject.testID = obj
    appointmentObject.save()
    return redirect('/lab_staff')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("lab_staff")
def deleteTest(request, pk):
    Test.objects.filter(testID=pk).update(result='')
    return redirect('/lab_tests')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("lab_staff")
def lab_search(request):
    # whatever user write in search box we get in query
    query = request.GET.get('search', False)
    patients = Patient.objects.all().filter(
        Q(patientID__icontains=query) | Q(name__icontains=query))
    return render(request, 'lab_staff/lab_staff_search.html', {'patients': patients})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("lab_staff")
def diagDetails(request, pk):
    obj = Diagnosis.objects.all().filter(patientID=pk)
    arr = []
    for i in obj:
        obj1 = Doctor.objects.get(doctorID=i.doctorID.doctorID)
        dict = {
            'diagnosisID': i.diagnosisID,
            'diagnosis': i.diagnosis,
            'recommendations': i.test_recommendation,
            'doctorName': obj1.name
        }
        arr.append(dict)
    return render(request, 'lab_staff/lab_diag_details.html', {'diag': arr})


'''Lab Staff View Ends Here'''

'''Insurance Staff View starts here'''


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("insurance_staff")
def denyClaim(request, pk):
    obj = Insurance.objects.get(request_id=pk)
    obj1 = Payment.objects.get(paymentID=obj.paymentID.paymentID)
    obj.status = 'denied'
    obj1.status = 'insurance denied'
    obj.save()
    obj1.save()
    return redirect('/insurance_staff')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("insurance_staff")
def approveClaim(request, pk):
    obj = Insurance.objects.get(request_id=pk)
    obj.status = 'approved'
    obj.save()
    return redirect('/insurance_staff')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("insurance_staff")
def authorizeFund(request, pk):
    obj = Insurance.objects.get(request_id=pk)
    obj1 = Payment.objects.get(paymentID=obj.paymentID.paymentID)
    obj1.status = 'completed'
    obj1.save()
    return redirect('/insurance_staff_review')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("insurance_staff")
def claimDisb(request):
    obj = Insurance.objects.all().filter(status='approved')
    arr = []
    for i in obj:
        obj1 = Patient.objects.get(patientID=i.patientID.patientID)
        obj2 = Payment.objects.get(paymentID=i.paymentID.paymentID)
        if(obj2.status != 'completed'):
            dict = {
                'patientName': obj1.name,
                'insuranceID': obj1.insuranceID,
                'amount': obj2.amount,
                'requestID': i.request_id
            }
        if(obj2.status != 'completed'):
            arr.append(dict)

    return render(request, 'insurance_staff/insurance_staff_review.html', {'disbursal': arr})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("insurance_staff")
def viewClaim(request):
    obj = Insurance.objects.all().filter(status='initiated')
    arr = []
    for i in obj:
        obj1 = Patient.objects.get(patientID=i.patientID.patientID)
        obj2 = Payment.objects.get(paymentID=i.paymentID.paymentID)
        dict = {
            'patientName': obj1.name,
            'insuranceID': obj1.insuranceID,
            'amount': obj2.amount,
            'requestID': i.request_id
        }
        arr.append(dict)

    return render(request, 'insurance_staff/insurance_staff.html', {'claims': arr})


'''Insurance Staff View ends here'''



''''------------------Hospital Staff View------------------- '''
# To show appointments to hospital staff for approval
@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_appointment(request):
    # those whose approval are needed
    appointments = Appointment.objects.all().filter(status='requested')
    appt = []
    for i in appointments:
        patient = Patient.objects.get(patientID=i.patientID.patientID)
        doctor = Doctor.objects.get(doctorID=i.doctorID.doctorID)
        mydict = {
            'appointmentID': i.appointmentID,
            'date': i.date,
            'time': i.time,
            'type': i.type,
            'patientID': i.patientID,
            'doctorID': i.doctorID,
            'patientName': patient.name,
            'doctorName': doctor.name,
            'status': i.status,
            'diagnosisID': i.diagnosisID,
            'testID': i.testID,
            'paymentID': i.paymentID,
            'created_on': i.created_on
        }
        appt.append(mydict)
    return render(request, 'hospital_staff/hospital_staff_appointments.html', {'appointments': appt})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_appointment_approve(request, ID):
    appointment = Appointment.objects.get(appointmentID=ID)
    patient = Patient.objects.get(patientID=appointment.patientID.patientID)
    appointment.status = 'approved'
    appointment.save()
    if(patient.name == ''):
        request.session['_patient_id'] = patient.patientID
        return HttpResponseRedirect('/hospital_create_patients')
    return redirect('/hospital_staff_appointments')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_appointment_reject(request, ID):
    appointment = Appointment.objects.get(appointmentID=ID)
    appointment.status = 'rejected'
    appointment.save()
    return redirect('/hospital_staff_appointments')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_create_patients(request):
    # print(request.session)
    pID = request.session.get('_patient_id')
    print(pID)
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = forms.PatientUpdateForm(request.POST)
        if form.is_valid():
            obj = Patient.objects.get(patientID=pID)
            #obj = Patient()
            if form.cleaned_data['PatientName'] != '':
                obj.name = form.cleaned_data['PatientName']
            if form.cleaned_data['Age'] != '':
                obj.age = form.cleaned_data['Age']
            if form.cleaned_data['Gender'] != '':
                obj.gender = form.cleaned_data['Gender']
            if form.cleaned_data['Height'] != '':
                obj.height = form.cleaned_data['Height']
            if form.cleaned_data['Weight'] != '':
                obj.weight = form.cleaned_data['Weight']
            if form.cleaned_data['InsuranceID'] != '':
                obj.insuranceID = form.cleaned_data['InsuranceID']
            obj.save()
            return redirect('/hospital_staff_appointments')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = forms.PatientUpdateForm()
    return render(request, 'hospital_staff/hospital_create_patients.html', {'form': form})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_approved_appointment(request):
    # those whose approval are needed
    appointments = Appointment.objects.all().filter(status='approved')
    appt = []
    for i in appointments:
        patient = Patient.objects.get(patientID=i.patientID.patientID)
        doctor = Doctor.objects.get(doctorID=i.doctorID.doctorID)
        mydict = {
            'appointmentID': i.appointmentID,
            'date': i.date,
            'time': i.time,
            'type': i.type,
            'patientID': i.patientID,
            'doctorID': i.doctorID,
            'patientName': patient.name,
            'doctorName': doctor.name,
            'status': i.status
        }
        appt.append(mydict)
    tests = Test.objects.all().filter(status='approved')
    return render(request, 'hospital_staff/hospital_staff_create_payment.html', {'appointments': appt, 'tests': tests})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_complete_appointment(request, ID):
    appointment = Appointment.objects.get(appointmentID=ID)
    print(appointment.appointmentID)
    request.session['_appointment_id'] = appointment.appointmentID
    appointment.status = 'completed'
    appointment.save()

    return HttpResponseRedirect('/hospital_transaction')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_transaction(request):
    apptID = request.session.get('_appointment_id')
    print(apptID)
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = forms.CreatePaymentForm(request.POST)
        if form.is_valid():
            apptID = Appointment.objects.get(appointmentID=apptID)
            pID = apptID.patientID
            obj = Payment()
            obj.amount = form.cleaned_data['Amount']
            obj.appointmentID = apptID
            obj.patientID = pID
            obj.status = 'initiated'
            obj.save()
            return HttpResponseRedirect('/hospital_staff_create_payment/')

        # if a GET (or any other method) we'll create a blank form
    else:
        form = forms.CreatePaymentForm()
    return render(request, 'hospital_staff/hospital_staff_amount.html', {'form': form})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_test_transaction(request, testID):
    print(testID)
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = forms.CreatePaymentForm(request.POST)
        if form.is_valid():
            test = Test.objects.get(testID=testID)
            pID = test.patientID
            obj = Payment()
            obj.amount = form.cleaned_data['Amount']
            obj.testID = test
            obj.patientID = pID
            obj.status = 'initiated'
            obj.save()
            test.status = 'completed'
            test.save()
            return HttpResponseRedirect('/hospital_staff_create_payment/')

        # if a GET (or any other method) we'll create a blank form
    else:
        form = forms.CreatePaymentForm()
    return render(request, 'hospital_staff/hospital_staff_amount.html', {'form': form})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_search(request):
    # whatever user write in search box we get in query
    query = request.GET.get('search', False)
    patients = Patient.objects.all().filter(
        Q(patientID__icontains=query) | Q(name__icontains=query))
    return render(request, 'hospital_staff/hospital_search_patients.html', {'patients': patients})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_view_patients(request):
    patients = Patient.objects.all()
    return render(request, 'hospital_staff/hospital_search_patients.html', {'patients': patients})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_update_patients(request, ID):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = forms.PatientUpdateForm(request.POST)
        if form.is_valid():
            obj = Patient.objects.get(patientID=ID)
            if form.cleaned_data['PatientName'] != '':
                obj.name = form.cleaned_data['PatientName']
            if form.cleaned_data['Age'] != '':
                obj.age = form.cleaned_data['Age']
            if form.cleaned_data['Gender'] != '':
                obj.gender = form.cleaned_data['Gender']
            if form.cleaned_data['Height'] != '':
                obj.height = form.cleaned_data['Height']
            if form.cleaned_data['Weight'] != '':
                obj.weight = form.cleaned_data['Weight']
            if form.cleaned_data['InsuranceID'] != '':
                obj.insuranceID = form.cleaned_data['InsuranceID']
            obj.save()
            return redirect("hospital_patient_details", ID)

        # if a GET (or any other method) we'll create a blank form
    else:
        form = forms.PatientUpdateForm()
    return render(request, 'hospital_staff/hospital_update_patients.html', {'form': form})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_patient_details(request, pID):
    patient_details = Patient.objects.get(patientID=pID)
    appointments = Appointment.objects.all().filter(patientID=pID)
    appt = []
    for i in appointments:
        doctor = Doctor.objects.get(doctorID=i.doctorID.doctorID)
        if i.diagnosisID is None:
            mydict = {
                'appointmentID': i.appointmentID,
                'date': i.date,
                'time': i.time,
                'type': i.type,
                'doctorName': doctor.name,
                'status': i.status,
                'diagnosis': '',
                'prescription': '',
                'created_on': i.created_on
            }
        else:
            diagnosis = Diagnosis.objects.get(
                diagnosisID=i.diagnosisID.diagnosisID)
            mydict = {
                'appointmentID': i.appointmentID,
                'date': i.date,
                'time': i.time,
                'type': i.type,
                'doctorName': doctor.name,
                'status': i.status,
                'diagnosis': diagnosis.diagnosis,
                'prescription': diagnosis.prescription,
                'created_on': i.created_on
            }
        appt.append(mydict)
    test_details = Test.objects.all().filter(patientID=pID)
    test = []
    for i in test_details:
        mydict = {
            'testID': i.testID,
            'date': i.date,
            'time': i.time,
            'type': i.type,
            'status': i.status,
            'result': i.result,
        }
        test.append(mydict)
    return render(request, 'hospital_staff/hospital_view_patient_details.html', {'patient_details': patient_details, 'appointment_details': appt, 'test_details': test})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_view_lab_report(request, testID):
    lab_test_details = models.Test.objects.all().filter(testID=testID)
    return Render.render('hospital_staff/hospital_view_lab_report.html', {'lab_test_details': lab_test_details})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_create_bills(request):
    payment_details = Payment.objects.all().filter(status='completed')
    return render(request, 'hospital_staff/hospital_generate_bill.html', {'payment_details': payment_details})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("hospital_staff")
def hospital_bill(request, ID):
    payment_details = Payment.objects.get(paymentID=ID)
    if payment_details.appointmentID is None:
        test = Test.objects.get(testID=payment_details.testID.testID)
        patient = Patient.objects.get(patientID=test.patientID.patientID)
        bill = {
            'method': payment_details.method,
            'amount': payment_details.amount,
            'testType': test.type,
            'patientName': patient.name,
            'paymentID': payment_details.paymentID}
        return Render.render('hospital_staff/hospital_bill_test.html', {'bill': bill})
    if payment_details.testID is None:
        appointment = Appointment.objects.get(
            appointmentID=payment_details.appointmentID.appointmentID)
        patient = Patient.objects.get(
            patientID=appointment.patientID.patientID)
        doctor = Doctor.objects.get(doctorID=appointment.doctorID.doctorID)
        bill = {
            'method': payment_details.method,
            'amount': payment_details.amount,
            'doctorName': doctor.name,
            'patientName': patient.name,
            'paymentID': payment_details.paymentID}
        return Render.render('hospital_staff/hospital_bill_appointment.html', {'bill': bill})


'''---------------Hospital end-------------'''



# ---------------------------------------------------------------------------------
# ------------------------ PATIENT RELATED VIEWS START ------------------------------
# ---------------------------------------------------------------------------------
@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def patient(request):
    return render(request, 'Patient/patient.html', {"user": request.user})

# @app.route("/diagnosis")


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def patient_diagnosis_details(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    patient_diagnosis_details = models.Diagnosis.objects.all().filter(patientID=patientID)
    # print(patient_diagnosis_details)
    return render(request, 'Patient/diagnosis.html', {'patient_diagnosis_details': patient_diagnosis_details})

# @app.route("/prescription")


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def patient_prescription_details(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    patient_prescription_details = models.Diagnosis.objects.all().filter(patientID=patientID)
    return render(request, 'Patient/prescription.html', {'patient_prescription_details': patient_prescription_details})


# patient details views
@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def patient_details(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    patient = models.Patient.objects.filter(patientID=patientID)
    return render(request, 'Patient/patient_details.html', {'patient': patient, "user": request.user})


def update_patient_record(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    patient = Patient.objects.get(patientID=patientID)
    # print(patient)
    # patientForm=forms.PatientForm(request.POST,request.FILES)
    patientForm = forms.PatientForm(request.POST)

    if request.method == 'POST':
        # print("Hi from POST")
        # print(patientForm.data['age'])
        patient.name = patientForm.data['name']
        patient.age = patientForm.data['age']
        patient.gender = patientForm.data['gender']
        patient.height = patientForm.data['height']
        patient.weight = patientForm.data['weight']
        patient.insuranceID = patientForm.data['insuranceID']
        patient.save()

        # patientForm=forms.PatientForm(request.POST,request.FILES,instance=patient)
        # print(patientForm.errors)
        # patientForm['patientID']
        if patientForm.is_valid():
            pass

        patient = Patient.objects.get(patientID=patientID)
        # return redirect("{% url 'patient_details' patient.patientID %}")
        return redirect("patient_details", patient.patientID)

    mydict = {'patientForm': patientForm}
    return render(request, 'Patient/update_patient_details.html', context=mydict)


# Lab views
@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def patient_labtest_view(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    return render(request, 'Patient/labtest/labtest.html', {"user": request.user})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def request_test(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    # print(testform.data)
    # appt=models.Appointment.objects.get(patientID=patientID)
    # diag=models.Diagnosis.objects.get(diagnosisID=testform.data['diagnosisID'])

    test = Test()
    if request.method == 'POST':
        testform = forms.RequestLabTestForm(request.POST, patientID=patientID)
        token = testform.data['otp_token']
        if not match_token(request.user, token):
            raise PermissionDenied
        test.date = testform.data['date']
        test.time = testform.data['time']
        test.type = testform.data['type']
        # test.diagnosisID=appt.diagnosisID
        test.diagnosisID = models.Diagnosis.objects.get(
            diagnosisID=testform.data['diagnosisID'])
        # test.diagnosisID=appt.diagnosisID
        test.patientID = models.Patient.objects.get(patientID=patientID)
        test.status = 'requested'
        test.save()
        # Test.save(self)
        if testform.is_valid():
            pass
        return redirect('patient_view_lab_report', patientID)
    else:
        testform = forms.RequestLabTestForm(patientID=patientID)
    return render(request, 'Patient/labtest/request_labtest.html', {"patient": patient, "testform": testform})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def view_lab_report(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    lab_test_details = models.Test.objects.all().filter(patientID=patientID)
    Appt={}
    for tests in lab_test_details:
        Diag = models.Diagnosis.objects.all().filter(diagnosisID=tests.diagnosisID.diagnosisID)
        for d in Diag:
            Appt[tests.diagnosisID.diagnosisID] = d.appointmentID.appointmentID
    print(Appt) 
    
    return render(request, 'Patient/labtest/patient_view_lab_report.html', {'lab_test_details': lab_test_details, "Appt":Appt})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient", "doctor")
def view_one_lab_report(request, testID):
    lab_test_details = models.Test.objects.all().filter(testID=testID)
    Appt={}
    for tests in lab_test_details:
        Diag = models.Diagnosis.objects.all().filter(diagnosisID=tests.diagnosisID.diagnosisID)
        for d in Diag:
            Appt[tests.diagnosisID.diagnosisID] = d.appointmentID.appointmentID
    print(Appt) 
    return Render.render('Patient/labtest/patient_view_single_lab_report.html', {'lab_test_details': lab_test_details})

# Chatbot Views


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def get_bot_response(request):
    d = request.GET
    userText = d['msg']
    result = chatgui.chatbot_response(userText)
    return HttpResponse(result, content_type="text/plain")


# Appointment Views
@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def patient_appointment_view(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    return render(request, 'Patient/Appointment/appointment.html')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def patient_previous_appointment_view(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    patient_prev_appointments = models.Appointment.objects.all().filter(patientID=patientID)
    # print(patient_diagnosis_details)
    return render(request, 'Patient/Appointment/view-appoitnment.html', {'patient_prev_appointments': patient_prev_appointments})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def patient_book_appointment_view(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    appointmentForm = forms.PatientAppointmentForm(request.POST)
    print(appointmentForm.data)
    if request.method == 'POST':
        Appt = Appointment()
        Appt.date = appointmentForm.data['date']
        Appt.time = appointmentForm.data['time']
        # Appointment.type=appointmentForm.data['type']
        # Appt.doctorID = models.Doctor.objects.get(
        #     doctorID=appointmentForm.data['doctorID'])
        Appt.doctorID = models.Doctor.objects.get(
            doctorID=appointmentForm.data['doctorID'])
        if appointmentForm.data['doctorID'] == "GeneralDoctor":
            Appt.type = "General"
        else:
            Appt.type = "Specific"
        Appt.patientID = models.Patient.objects.get(patientID=patientID)
        Appt.status = 'requested'
        Appt.save()
        if appointmentForm.is_valid():
            pass
        return redirect('patient-view-appointment', patientID)
    return render(request, 'Patient/Appointment/book-appointment.html', {"user": request.user, "appointmentForm": appointmentForm})


# Payment and Transaction views
@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def make_payment(request, paymentID):
    patient_payments = models.Payment.objects.get(paymentID=paymentID)
    patientID = patient_payments.patientID
    if not (request.user.username == patientID.patientID):
        raise PermissionDenied
    print(patientID.patientID)
    if patient_payments.status == 'completed':
        return redirect('patient_payments', patientID.patientID)
    if request.method == 'POST':
        payform = forms.MakePaymentForm(request.POST)
        token = payform.data['otp_token']
        if not match_token(request.user, token):
            raise PermissionDenied
        patient_payments.method = payform.data['method']
        # print(payform.data['method'])
        if patient_payments.method == 'Insurance':
            patient_payments.status = 'pending'
            patient_payments.save()
            insurance = Insurance()
            insurance.paymentID = patient_payments
            insurance.patientID = patient_payments.patientID
            insurance.status = 'initiated'
            insurance.save()

        else:
            patient_payments.status = 'completed'
            patient_payments.save()

        if payform.is_valid():
            pass
        # print(patient_payments.amount)
        return redirect("patient_payments", patientID.patientID)
    else:
        payform = forms.MakePaymentForm()
    # mydict={'MakePaymentForm': payform}
    return render(request, 'Patient/payments_and_transactions/make_payment.html', {"patient_payments": patient_payments, "payform": payform})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("patient")
def patient_payments_details(request, patientID):
    if not (request.user.username == patientID):
        raise PermissionDenied
    patient_payments = models.Payment.objects.all().filter(patientID=patientID)
    return render(request, 'Patient/payments_and_transactions/patient_payments.html', {"patient_payments": patient_payments})


# ------------------------ PATIENT RELATED VIEWS END ------------------------------
# ---------------------------------------------------------------------------------




# ----------------------------------------doctor---------------------------------------------------


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor(request):
    return render(request, 'Doctor/doctorhome.html', {"user": request.user})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_view_appointment_view(request):
    appointments = models.Appointment.objects.all().filter(
        doctorID=request.user.username)
    l = []
    for i in appointments:
        patient = Patient.objects.get(patientID=i.patientID.patientID)
        doctor = Doctor.objects.get(doctorID=i.doctorID.doctorID)
        mydict = {
            'appointmentID': i.appointmentID,
            'date': i.date,
            'time': i.time,
            'type': i.type,
            'patientID': i.patientID,
            'doctorID': i.doctorID,
            'patientName': patient.name,
            'doctorName': doctor.name,
            'status': i.status,
            'diagnosisID': i.diagnosisID,
            'testID': i.testID,
            'paymentID': i.paymentID,
            'created_on': i.created_on
        }
        l.append(mydict)
    return render(request, 'Doctor/doctor_view_appointment_view.html', {'appointments': l})

# patient records button views start here


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_view_patientlist(request):
    appointments = models.Appointment.objects.all().filter(
        doctorID=request.user.username)
    # patients=models.Patient.objects.all().filter(patientID=appointments.patientID)
    l = []
    for i in appointments:
        p = models.Patient.objects.get(patientID=i.patientID.patientID)
        # print(i.diagnosisID)
        if i.testID:
            testID = i.testID.testID
        else:
            testID = 'None'
        if i.diagnosisID is None:
            # print('I am in if')
            mydict = {
                'appointmentID': i.appointmentID,
                'name': p.name,
                'age': p.age,
                'gender': p.gender,
                'patientID': p.patientID,
                'doctorID': i.doctorID,
                'height': p.height,
                'weight': p.weight,
                # 'diagnosisID' : i.diagnosisID,
                'diagnosis': 'null',
                'test_recommendation': 'null',
                'prescription': 'null',
                'testID': testID
            }
            # print(i.testID)

        else:
            # print('I am in else')
            d = Diagnosis.objects.all().filter(appointmentID=i.appointmentID)
            # print(d)
            for a in d:
                # print(i.patientID.patientID)
                # print(a.diagnosis)
                mydict = {
                    'appointmentID': i.appointmentID,
                    'name': p.name,
                    'age': p.age,
                    'gender': p.gender,
                    'patientID': p.patientID,
                    'doctorID': i.doctorID,
                    'height': p.height,
                    'weight': p.weight,
                    # 'diagnosisID': i.diagnosisID,
                    'diagnosis': a.diagnosis,
                    'test_recommendation': a.test_recommendation,
                    'prescription': a.prescription,
                    'testID': testID
                }
            # print(i.testID)

        l.append(mydict)
    return render(request, 'Doctor/doctor_view_patientlist.html', {'patients': l})

# @login_required
# @otp_required(login_url="account/two_factor/setup/")
# @check_view_permissions("doctor")
# def doctor_appointmentID_search_view(request):
#     # query stores the input given in search bar
#     query = request.GET['query']
#     # patients=models.Patient.objects.all().filter(doctorId=request.user.id).filter(Q(patientID__icontains=query)|Q(name__icontains=query))
#     appointments=models.Appointment.objects.all().filter(doctorId=request.user.id).filter(Q(patientID__icontains=query)|Q(appointmentID__icontains=query)|Q(date__icontains=query))
#     return render(request,'Doctor/doctor_view_appointment_view.html',{'appointments':appointments})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_create_prescription_view(request, ID):
    a = Appointment.objects.get(appointmentID=ID)
    p = Patient.objects.get(patientID=a.patientID.patientID)
    CreatePrescription = forms.CreatePrescription()

    if request.method == 'POST':
        if a.diagnosisID is None or a.diagnosisID == 'null':
            # print('asdfghjk')
            diag = Diagnosis()
            diag.prescription = CreatePrescription.data['prescription']
            diag.doctorID = models.Doctor.objects.get(
                doctorID=request.user.username)
            diag.patientID = models.Patient.objects.get(patientID=p.patientID)
            print(diag.patientID)
            diag.appointmentID = models.Appointment.objects.get(
                appointmentID=ID)
            a.diagnosisID = diag
            diag.save()
            a.save()
            return redirect('doctor_view_patientlist')
        else:
            d = Diagnosis.objects.get(appointmentID=ID)
            d.prescription = CreatePrescription.data['prescription']
            d.save()
        return redirect('doctor_view_patientlist')

    mydict = {'CreatePrescription': CreatePrescription}
    return render(request, 'Doctor/doctor_create_prescription.html', context=mydict)


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_search_view(request):
    if request.method == "POST":
        searched = request.POST['searched']
        patients = Patient.objects.filter(patientID__contains=searched)

        return render(request, 'Doctor/doctor_search.html', {'searched': searched, 'patients': patients})
    else:
        return render(request, 'Doctor/doctor_search.html', {})

    #     def hospital_search(request):
    # # whatever user write in search box we get in query
    # query = request.GET.get('search',False)
    # a=Appointment.objects.filter(appointmentID__contains = query)
    # return render(request,'Doctor/doctor_search.html',{'a':a})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_view_labreport_view(request, ID):
    if(ID == "None"):
        return HttpResponse("No test report to show")
    lab_test_details = models.Test.objects.get(testID=ID)
    print(lab_test_details)
    return redirect('patient_view_single_lab_report', testID = ID)


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_recommend_labtest_view(request, ID):
    # d=Diagnosis.objects.filter(appointmentID=ID)
    # d=d[0]
    a = Appointment.objects.get(appointmentID=ID)
    p = Patient.objects.get(patientID=a.patientID.patientID)
    RecommendLabTest = forms.RecommendLabTest(request.POST)
    if request.method == 'POST':
        if a.diagnosisID is None or a.diagnosisID == 'null':
            print('asdfghjk')
            diag = Diagnosis()
            diag.test_recommendation = RecommendLabTest.data['test_recommendation']
            diag.doctorID = models.Doctor.objects.get(
                doctorID=request.user.username)
            diag.patientID = models.Patient.objects.get(patientID=p.patientID)
            diag.appointmentID = models.Appointment.objects.get(
                appointmentID=ID)
            a.diagnosisID = diag
            diag.save()
            a.save()
            return redirect('doctor_view_patientlist')
        else:
            di = models.Diagnosis.objects.get(appointmentID=ID)
            print('di', di)
            di.test_recommendation = RecommendLabTest.data['test_recommendation']
            di.save()
            # d.test_recommendation=RecommendLabTest.data['test_recommendation']
            # d.save()
            return redirect('doctor_view_patientlist')

    mydict = {'RecommendLabTest': RecommendLabTest}
    return render(request, 'Doctor/doctor_recommendlabtest.html', context=mydict)


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_createpatientdiagnosis_view(request, ID):
    # d=models.Diagnosis.objects.get(appointmentID=ID)
    # print('asdfghj', d)
    a = Appointment.objects.get(appointmentID=ID)
    p = Patient.objects.get(patientID=a.patientID.patientID)
    EditDiagnosisForm = forms.EditDiagnosisForm(request.POST)

    if request.method == 'POST':
        if EditDiagnosisForm.is_valid():
            print("EditDiagnosisForm is valid")
            if a.diagnosisID is None or a.diagnosisID == 'null':
                # print('asdfghjk')
                diag = Diagnosis()
                diag.diagnosis = EditDiagnosisForm.data['diagnosis']
                diag.doctorID = models.Doctor.objects.get(
                    doctorID=request.user.username)
                diag.patientID = models.Patient.objects.get(
                    patientID=p.patientID)
                diag.appointmentID = models.Appointment.objects.get(
                    appointmentID=ID)
                a.diagnosisID = diag
                diag.save()
                a.save()
                # return redirect('doctor_view_patientlist')
            else:
                # print(di)
                print('ID', a.appointmentID)
                print('diag ID', a.diagnosisID.diagnosisID)
                d = models.Diagnosis.objects.get(appointmentID=ID)
                print(d)
                d.diagnosis = EditDiagnosisForm.data['diagnosis']
                a.diagnosisID = d
                d.save()
                a.save()
            return redirect('doctor_view_patientlist')

    mydict = {'EditDiagnosisForm': EditDiagnosisForm}
    return render(request, 'Doctor/doctor_createpatientdiagnosis_view.html', context=mydict)


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_update_patients(request, ID):
    patient = Patient.objects.get(patientID=ID)
    patientForm = forms.PatientForm(request.POST)

    if request.method == 'POST':
        # print("Hi from POST")
        # print(patientForm.data['age'])
        patient.name = patientForm.data['name']
        patient.age = patientForm.data['age']
        patient.gender = patientForm.data['gender']
        patient.height = patientForm.data['height']
        patient.weight = patientForm.data['weight']
        patient.save()
        if patientForm.is_valid():
            print("patientForm is valid")
            patient.save()
            # patient.save(force_update=True)

        patient = Patient.objects.get(patientID=ID)
        # return redirect("{% url 'patient_details' patient.patientID %}")
        return redirect('doctor_view_patientlist')

    mydict = {'patientForm': patientForm}
    return render(request, 'Doctor/doctor_update_patient.html', context=mydict)


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_delete_diagnosis(request, ID):
    models.Diagnosis.objects.filter(appointmentID=ID).update(diagnosis='null')
    return redirect('doctor_view_patientlist')


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_search_appointment(request, ID):
    # patient_details = Patient.objects.get(patientID = pID)
    appointments = models.Appointment.objects.all().filter(
        doctorID=request.user.username)
    l = []
    for i in appointments:
        patient = Patient.objects.get(patientID=i.patientID.patientID)
        doctor = Doctor.objects.get(doctorID=i.doctorID.doctorID)
        mydict = {
            # 'appointmentID': i.appointmentID,
            'date': i.date,
            'time': i.time,
            'type': i.type,
            'patientID': i.patientID,
            'doctorID': i.doctorID,
            'patientName': patient.name,
            'doctorName': doctor.name,
            'status': i.status,
            'diagnosisID': i.diagnosisID,
            'testID': i.testID,
            'paymentID': i.paymentID,
            'created_on': i.created_on
        }
        l.append(mydict)
    return render(request, 'Doctor/doctor_search_appointment.html', {'l': l})


@login_required
@otp_required(login_url="account/two_factor/setup/")
@check_view_permissions("doctor")
def doctor_book_appointment(request, ID):
    print('id', ID)
    ap = Appointment.objects.get(appointmentID=ID)
    appointmentForm = forms.DoctorAppointmentForm(request.POST)
    print(appointmentForm.data)
    if request.method == 'POST':
        a = Appointment()
        diag = Diagnosis()
        diag.doctorID = models.Doctor.objects.get(doctorID=request.user.username)
        diag.patientID = models.Patient.objects.get(patientID=ap.patientID.patientID)
        diag.appointmentID = models.Appointment.objects.get(appointmentID=ID)
        print(diag.appointmentID)
        diag.diagnosis = "Null"
        a.date = appointmentForm.data['date']
        a.time = appointmentForm.data['time']
        ap.diagnosisID = diag
        a.diagnosisID = ap.diagnosisID.diagnosisID
        # print(ap.diagnosisID)
        diag.save()
        a.doctorID = models.Doctor.objects.get(doctorID=request.user.username)
        a.patientID = models.Patient.objects.get(patientID=ap.patientID.patientID)
        print('appointmentID', ap.appointmentID)
        if a.doctorID.doctorID == request.user.username:
            a.type = "General"
        else:
            a.type = "Specific"
        a.status = 'approved'
        a.save()
        if appointmentForm.is_valid():
            a.status = 'approved'
            a.save()
        return redirect('doctor_appointment')
    return render(request, 'Doctor/doctor_book_appointment.html', {'appointmentForm': appointmentForm})
