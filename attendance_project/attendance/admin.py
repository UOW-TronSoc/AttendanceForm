# attendance/admin.py

from django.contrib import admin
from .models import Team, Member, Meeting, AttendanceFeedback


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    list_filter = ("teams",)
    filter_horizontal = ("teams",)


class AttendanceFeedbackInline(admin.TabularInline):
    model = AttendanceFeedback
    extra = 0
    fields = ("member", "attended", "engagement", "effort", "contribution")
    readonly_fields = ()
    show_change_link = True


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("primary_team", "datetime", "attendance_count")
    list_filter = ("primary_team", "datetime")
    search_fields = ("primary_team__name",)
    date_hierarchy = "datetime"
    inlines = [AttendanceFeedbackInline]

    def attendance_count(self, obj):
        return obj.attendance_feedback.count()
    attendance_count.short_description = "# Attendees"


@admin.register(AttendanceFeedback)
class AttendanceFeedbackAdmin(admin.ModelAdmin):
    list_display = ("meeting", "member", "attended", "engagement", "effort", "contribution")
    list_filter = ("attended", "engagement", "effort", "contribution")
    search_fields = ("member__name", "meeting__primary_team__name")
    raw_id_fields = ("meeting", "member")
