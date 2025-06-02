from django.urls import path
from .views import *

app_name = "attendance"

urlpatterns = [
    path("new/", CreateMeetingView.as_view(), name="meeting_create"),
    path("feedback/", MeetingFeedbackView.as_view(), name="meeting_feedback"),
    path("success/<int:pk>/", MeetingSuccessView.as_view(), name="meeting_success"),
    path("list/", MeetingListView.as_view(), name="list_meetings"),
    path("members/add/", AddMemberAjaxView.as_view(), name="add_member_ajax"),
    path("detail/<int:pk>/", MeetingDetailView.as_view(), name="detail_meeting"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),

]
