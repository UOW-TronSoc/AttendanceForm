from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from .forms import *
from .models import *
from django import forms
from django.forms import formset_factory
from django.views.generic import DetailView, ListView, TemplateView

from django.db.models import Count, Avg
import json


from django.http import JsonResponse, HttpResponseBadRequest
from django.middleware.csrf import get_token


import datetime

class CreateMeetingView(View):
    template_name = "attendance/meeting_form.html"

    def get(self, request):
        form = MeetingForm()
        teams = Team.objects.all()
        return render(request, self.template_name, {
            "form": form,
            "teams": teams,
        })

    def post(self, request):
        form = MeetingForm(request.POST)
        if form.is_valid():
            # Stash meeting_data without "notes"
            meeting_data = {
                "datetime": form.cleaned_data["datetime"].isoformat(),
                "primary_team_id": form.cleaned_data["primary_team"].pk,
            }
            member_ids = [m.pk for m in form.cleaned_data["attending_members"]]
            request.session["new_meeting_data"] = meeting_data
            request.session["new_meeting_member_ids"] = member_ids
            return redirect(reverse("attendance:meeting_feedback"))
        # If invalid, re-render (including teams)
        teams = Team.objects.all()
        return render(request, self.template_name, {
            "form": form,
            "teams": teams,
        })


class MeetingFeedbackView(View):
    template_name = "attendance/feedback_form.html"
    FeedbackFormSet = formset_factory(SingleFeedbackForm, extra=0)

    def get(self, request):
        meeting_data = request.session.get("new_meeting_data")
        member_ids = request.session.get("new_meeting_member_ids", [])
        if not meeting_data or not member_ids:
            return redirect(reverse("attendance:meeting_create"))

        members = Member.objects.filter(pk__in=member_ids)
        formset = self.FeedbackFormSet(initial=[{} for _ in members])
        paired = list(zip(formset.forms, members))

        # Pass BOTH 'paired' and 'formset' so template can show errors
        return render(request, self.template_name, {
            "paired": paired,
            "formset": formset,
        })

    def post(self, request):
        meeting_data = request.session.get("new_meeting_data")
        member_ids = request.session.get("new_meeting_member_ids", [])
        if not meeting_data or not member_ids:
            return redirect(reverse("attendance:meeting_create"))

        members = Member.objects.filter(pk__in=member_ids)
        formset = self.FeedbackFormSet(request.POST)

        if formset.is_valid() and len(formset) == len(members):
            dt = datetime.datetime.fromisoformat(meeting_data["datetime"])
            team_pk = meeting_data["primary_team_id"]

            meeting = Meeting.objects.create(
                datetime=dt,
                primary_team_id=team_pk,
                # notes field was removed earlier
            )

            for feedback_data, member in zip(formset.cleaned_data, members):
                AttendanceFeedback.objects.create(
                    meeting=meeting,
                    member=member,
                    attended=True,
                    engagement=feedback_data["engagement"],
                    effort=feedback_data["effort"],
                    contribution=feedback_data["contribution"],
                )

            # Clean up session
            del request.session["new_meeting_data"]
            del request.session["new_meeting_member_ids"]
            return redirect(reverse("attendance:meeting_success", args=[meeting.pk]))
        else:
            # STILL pass formset so any errors become visible
            paired = list(zip(formset.forms, members))
            return render(request, self.template_name, {
                "paired": paired,
                "formset": formset,
            })



class MeetingSuccessView(DetailView):
    model = Meeting
    template_name = "attendance/meeting_success.html"
    context_object_name = "meeting"


class MeetingListView(ListView):
    model = Meeting
    template_name = "attendance/meeting_list.html"
    context_object_name = "meetings"
    paginate_by = 20  # if you expect many

class MeetingDetailView(DetailView):
    model = Meeting
    template_name = "attendance/meeting_detail.html"
    context_object_name = "meeting"


class AddMemberAjaxView(View):
    """
    Accepts POST JSON (or form-encoded) with 'name' and 'teams' list.
    Creates the Member, and returns JSON with { id, name, team_ids }.
    """
    def post(self, request):
        # Bind the MemberForm to POST data
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save()
            # After saving, gather the member’s team IDs as CSV
            team_ids = [str(t.pk) for t in member.teams.all()]
            return JsonResponse({
                "id": member.pk,
                "name": member.name,
                "team_ids": ",".join(team_ids),
            })
        else:
            # Return form errors as JSON
            return JsonResponse({"errors": form.errors}, status=400)



class AnalyticsView(TemplateView):
    template_name = "attendance/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1) Number of meetings per team
        meetings_per_team_qs = (
            Meeting.objects
            .values("primary_team__name")
            .annotate(total_meetings=Count("id"))
            .order_by("primary_team__name")
        )
        team_labels = [entry["primary_team__name"] for entry in meetings_per_team_qs]
        team_counts = [entry["total_meetings"] for entry in meetings_per_team_qs]

        # 2) Average engagement per meeting (ordered by meeting datetime)
        avg_engagement_qs = (
            AttendanceFeedback.objects
            .values("meeting__id", "meeting__datetime")
            .annotate(avg_engagement=Avg("engagement"))
            .order_by("meeting__datetime")
        )
        engagement_labels = [
            entry["meeting__datetime"].strftime("%Y-%m-%d") for entry in avg_engagement_qs
        ]
        engagement_values = [
            float(entry["avg_engagement"] or 0) for entry in avg_engagement_qs
        ]

        # 3) Top 5 most‐attending members
        top_members_qs = (
            AttendanceFeedback.objects
            .filter(attended=True)
            .values("member__name")
            .annotate(attendance_count=Count("id"))
            .order_by("-attendance_count")[:5]
        )

        # 4) Per‐member average feedback (across all meetings)
        member_avg_qs = (
            AttendanceFeedback.objects
            .filter(attended=True)
            .values("member__name")
            .annotate(
                avg_engagement=Avg("engagement"),
                avg_effort=Avg("effort"),
                avg_contribution=Avg("contribution")
            )
            .order_by("member__name")
        )
        # Convert to list of dicts for template
        member_feedback_list = []
        for entry in member_avg_qs:
            member_feedback_list.append({
                "name": entry["member__name"],
                "avg_engagement": round(entry["avg_engagement"] or 0, 2),
                "avg_effort": round(entry["avg_effort"] or 0, 2),
                "avg_contribution": round(entry["avg_contribution"] or 0, 2),
            })

        # JSON‐encode data for charts if needed
        context["team_labels_json"]       = json.dumps(team_labels)
        context["team_counts_json"]       = json.dumps(team_counts)
        context["engagement_labels_json"] = json.dumps(engagement_labels)
        context["engagement_values_json"] = json.dumps(engagement_values)
        context["top_members"]            = list(top_members_qs)
        context["member_feedback_list"]   = member_feedback_list

        return context
