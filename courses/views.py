from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Block
from .models import Course, Enrollment, Material, Feedback
from .forms import CourseForm, MaterialForm, FeedbackForm, StatusUpdateForm
from .tasks import notify_new_enrollment, notify_new_material, notify_new_feedback

User = get_user_model()

def is_teacher(user):
    return getattr(user, "role", None) == User.TEACHER

def is_student(user):
    return getattr(user, "role", None) == User.STUDENT

# ---------- DASHBOARD ----------
@login_required
def dashboard_view(request):
    status_form = StatusUpdateForm()
    if is_teacher(request.user):
        courses = Course.objects.filter(instructor=request.user)
        return render(request, "dashboard/teacher_dashboard.html", {
            "courses": courses,
            "status_form": status_form,
        })
    else:
        enrollments = Enrollment.objects.filter(student=request.user).select_related("course")
        enrolled_courses = [e.course for e in enrollments]
        blocked_teacher_ids = Block.objects.filter(blocked=request.user).values_list("teacher_id", flat=True)
        available_courses = (
            Course.objects.exclude(pk__in=[c.pk for c in enrolled_courses])
                          .exclude(instructor_id__in=blocked_teacher_ids)
        )
        return render(request, "dashboard/student_dashboard.html", {
            "enrollments": enrollments,
            "available_courses": available_courses,
            "status_form": status_form,
        })

@login_required
def post_status(request):
    if request.method == "POST":
        form = StatusUpdateForm(request.POST)
        if form.is_valid():
            su = form.save(commit=False)
            su.user = request.user
            su.save()
            messages.success(request, "Status posted.")
        else:
            messages.error(request, "Could not post status.")
    return redirect("home")

# ---------- COURSES ----------
@login_required
def course_create(request):
    if not is_teacher(request.user):
        return HttpResponseForbidden()
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, "Course created.")
            return redirect("course_detail", course_id=course.id)
    else:
        form = CourseForm()
    return render(request, "courses/course_form.html", {"form": form})

@login_required
def course_list(request):
    courses = Course.objects.all().order_by("-created_at")
    return render(request, "courses/course_list.html", {"courses": courses})

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor")
                      .prefetch_related(
                          "materials",
                          Prefetch("feedbacks", queryset=Feedback.objects.select_related("student").order_by("-created_at"))
                      ),
        pk=course_id
    )
    enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
    is_instructor = is_teacher(request.user) and course.instructor_id == request.user.id
    roster = []
    if is_instructor:
        roster = Enrollment.objects.filter(course=course).select_related("student").order_by("student__username")
    can_chat = is_instructor or enrolled
    return render(request, "courses/course_detail.html", {
        "course": course,
        "enrolled": enrolled,
        "is_instructor": is_instructor,
        "roster": roster,
        "can_chat": can_chat,
    })

@login_required
def enroll_in_course(request, course_id):
    if not is_student(request.user):
        return HttpResponseForbidden()
    course = get_object_or_404(Course, pk=course_id)

    if Block.objects.filter(teacher=course.instructor, blocked=request.user).exists():
        messages.error(request, "You cannot enroll: the instructor has blocked you.")
        return redirect("course_detail", course_id=course.id)

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )
    if created:
        notify_new_enrollment.delay(enrollment.id)
        messages.success(request, "Enrolled successfully.")
    else:
        messages.info(request, "You are already enrolled.")
    return redirect("course_detail", course_id=course.id)

@login_required
def unenroll_student(request, course_id, student_id):
    """Teacher action: remove a student from their course."""
    if not is_teacher(request.user):
        return HttpResponseForbidden()
    course = get_object_or_404(Course, pk=course_id, instructor=request.user)
    qs = Enrollment.objects.filter(course=course, student_id=student_id)
    if qs.exists():
        qs.delete()
        messages.success(request, "Student unenrolled from the course.")
    else:
        messages.info(request, "That student is not enrolled in this course.")
    return redirect("course_detail", course_id=course.id)

@login_required
def material_upload(request, course_id):
    if not is_teacher(request.user):
        return HttpResponseForbidden()
    course = get_object_or_404(Course, pk=course_id, instructor=request.user)
    if request.method == "POST":
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course
            material.save()
            notify_new_material.delay(material.id)
            messages.success(request, "Material uploaded.")
            return redirect("course_detail", course_id=course.id)
    else:
        form = MaterialForm()
    return render(request, "courses/material_form.html", {"form": form, "course": course})

@login_required
def give_feedback(request, course_id):
    if not is_student(request.user):
        return HttpResponseForbidden()
    course = get_object_or_404(Course, pk=course_id)

    if not Enrollment.objects.filter(course=course, student=request.user).exists():
        messages.error(request, "You must be enrolled to leave feedback.")
        return redirect("course_detail", course_id=course.id)

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.course = course
            fb.student = request.user
            fb.save()
            notify_new_feedback.delay(fb.id)
            messages.success(request, "Thanks! Your feedback has been posted.")
            return redirect("course_detail", course_id=course.id)
    else:
        form = FeedbackForm()
    return render(request, "courses/feedback_form.html", {"form": form, "course": course})
