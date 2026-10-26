from django.urls import path
from apps.jobs.views import JobCategoryListView, SkillListView

urlpatterns = [
    path("categories/", JobCategoryListView.as_view(), name="job-category-list"),
    path("skills/", SkillListView.as_view(), name="skill-list"),
]
