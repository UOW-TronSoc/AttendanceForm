from django import forms
from .models import *
from django.forms import ModelForm, formset_factory

class MeetingForm(forms.ModelForm):
    attending_members = forms.ModelMultipleChoiceField(
        queryset=Member.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Attending Members",
        help_text="Select all members who attended this meeting (at least 2)."
    )

    class Meta:
        model = Meeting
        # Drop "notes" here:
        fields = ["datetime", "primary_team"]
        widgets = {
            "datetime": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "required": True,
                }
            ),
            "primary_team": forms.Select(attrs={"class": "form-control", "required": True}),
        }
        labels = {
            "datetime": "Meeting Date & Time",
            "primary_team": "Primary Team",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize attending_members queryset to all members (we’ll filter by JS)
        self.fields["attending_members"].queryset = Member.objects.all()
        self.fields["attending_members"].widget.attrs.update({"required": True})

    def clean_attending_members(self):
        members = self.cleaned_data.get("attending_members")
        if members.count() < 2:
            raise forms.ValidationError("At least 2 members must attend.")
        return members




class SingleFeedbackForm(forms.Form):

    engagement = forms.TypedChoiceField(
        label="Engagement",
        choices=AttendanceFeedback.LIKERT_CHOICES_ENGAGEMENT,
        widget=forms.RadioSelect,
        coerce=int,
        required=True,
        error_messages={"required": "Please choose an engagement level."},
    )

    effort = forms.TypedChoiceField(
        label="Effort",
        choices=AttendanceFeedback.LIKERT_CHOICES_EFFORT,
        widget=forms.RadioSelect,
        coerce=int,
        required=True,
        error_messages={"required": "Please choose an effort level."},
    )

    contribution = forms.TypedChoiceField(
        label="Contribution",
        choices=AttendanceFeedback.LIKERT_CHOICES_CONTRIBUTION,
        widget=forms.RadioSelect,
        coerce=int,
        required=True,
        error_messages={"required": "Please choose a contribution level."},
    )

        


FeedbackFormSet = formset_factory(
    SingleFeedbackForm,
    extra=0,  # we’ll set initial data based on how many members
    min_num=1,
    validate_min=True,
)


class MemberForm(forms.ModelForm):
    """
    A simple ModelForm for creating a new Member.
    We ask for name + teams (since a member can belong to multiple teams).
    """
    class Meta:
        model = Member
        fields = ["name", "teams"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter member name",
                "required": True,
            }),
            "teams": forms.SelectMultiple(attrs={
                "class": "form-select",
                # You can add size or data-live-search if you want a fancier multi-select.
            }),
        }
        labels = {
            "name": "Member Name",
            "teams": "Teams (hold Ctrl/Cmd to select multiple)",
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if Member.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A member with this name already exists.")
        return name
