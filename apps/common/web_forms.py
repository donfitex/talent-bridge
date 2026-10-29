from django import forms
from django.contrib.auth.forms import AuthenticationForm
from apps.users.serializers import UserRegistrationSerializer
from apps.users.models import UserRole
from apps.jobs.models import Job
from apps.companies.models import Company
from apps.candidates.models import CandidateProfile
from apps.applications.models import ApplicationStatus


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")


class RegistrationForm(forms.Form):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    role = forms.ChoiceField(choices=[(UserRole.CANDIDATE, "Candidate"), (UserRole.EMPLOYER, "Employer")])
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        data = super().clean()
        if self.errors:
            return data
        self.serializer = UserRegistrationSerializer(data=data, context={"role": data["role"]})
        if not self.serializer.is_valid():
            raise forms.ValidationError(str(self.serializer.errors))
        return data

    def save(self):
        return self.serializer.save()


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["company", "title", "description", "responsibilities", "requirements", "category",
            "location", "country", "employment_type", "workplace_type", "experience_level",
            "salary_min", "salary_max", "salary_currency", "application_deadline"]
        widgets = {"application_deadline": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = Company.objects.all() if user.is_admin_user else Company.objects.filter(memberships__user=user, memberships__is_active=True)


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "description", "industry", "company_size", "website", "location", "country"]


class CandidateForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ["professional_title", "biography", "location", "country", "phone", "years_of_experience", "is_public", "is_contact_visible"]


class ApplicationForm(forms.Form):
    resume = forms.ModelChoiceField(queryset=None)
    cover_letter = forms.CharField(widget=forms.Textarea, required=False, max_length=20000)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.resumes.models import Resume
        self.fields["resume"].queryset = Resume.objects.filter(candidate__user=user)


class ResumeForm(forms.Form):
    title = forms.CharField(max_length=255)
    file = forms.FileField()
    is_default = forms.BooleanField(required=False)


class PipelineForm(forms.Form):
    status = forms.ChoiceField(choices=ApplicationStatus.choices)
    note = forms.CharField(widget=forms.Textarea, required=False, max_length=5000)


class InterviewForm(forms.Form):
    interviewer = forms.ModelChoiceField(queryset=None)
    starts_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    ends_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    location = forms.CharField(max_length=500)

    def __init__(self, *args, application, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.users.models import User
        self.fields["interviewer"].queryset = User.objects.filter(employer_memberships__company=application.job.company,
            employer_memberships__is_active=True, is_active=True)
