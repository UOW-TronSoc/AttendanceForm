from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Member(models.Model):
    """
    A person who may belong to multiple teams. 
    """
    name = models.CharField(max_length=100)
    teams = models.ManyToManyField(Team, related_name="members", blank=True)

    def __str__(self):
        return self.name


class Meeting(models.Model):
    """
    Stores a single meeting: date/time, primary team, and optional notes.
    """
    datetime = models.DateTimeField()
    primary_team = models.ForeignKey(
        Team, on_delete=models.PROTECT, related_name="meetings"
    )
    notes = models.TextField(
        blank=True,
        help_text="General notes for the meeting (absences, blockers, etc.)",
    )

    def __str__(self):
        return f"{self.primary_team.name} on {self.datetime:%Y-%m-%d %H:%M}"


class AttendanceFeedback(models.Model):
    """
    One record per (meeting, member). 
    If “attended=False,” ratings may be left blank or set to some default.
    """
    LIKERT_CHOICES_ENGAGEMENT = [
        (1, "Not at all engaged"),
        (2, "Not very engaged"),
        (3, "Neutral"),
        (4, "Somewhat engaged"),
        (5, "Very engaged"),
    ]
    LIKERT_CHOICES_EFFORT = [
        (1, "Not at all"),
        (2, "Not very"),
        (3, "Neutral"),
        (4, "Somewhat"),
        (5, "High Effort"),
        (6, "Low Effort–Exempt"),  # if circumstances limited.
    ]
    LIKERT_CHOICES_CONTRIBUTION = [
        (1, "Not at all"),
        (2, "Not very"),
        (3, "Neutral"),
        (4, "Somewhat"),
        (5, "A lot"),
    ]

    meeting = models.ForeignKey(
        Meeting, on_delete=models.CASCADE, related_name="attendance_feedback"
    )
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    attended = models.BooleanField(default=True)
    engagement = models.PositiveSmallIntegerField(
        choices=LIKERT_CHOICES_ENGAGEMENT, null=True, blank=True
    )
    effort = models.PositiveSmallIntegerField(
        choices=LIKERT_CHOICES_EFFORT, null=True, blank=True
    )
    contribution = models.PositiveSmallIntegerField(
        choices=LIKERT_CHOICES_CONTRIBUTION, null=True, blank=True
    )

    class Meta:
        unique_together = ("meeting", "member")

    def __str__(self):
        return f"{self.member.name} @ {self.meeting}"
