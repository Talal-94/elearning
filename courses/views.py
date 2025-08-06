from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Course, Enrollment
from .forms import CourseForm, MaterialForm, FeedbackForm, StatusUpdateForm, StatusUpdateForm
from .tasks import (
    notify_new_enrollment,
    notify_new_material,
    notify_new_feedback,
)

User = get_user_model()

def is_teacher(user):
    return user.role == User.TEACHER

@login_required
@user_passes_test(is_teacher)
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            return redirect('home')
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form})

@login_required
def course_list(request):
    courses = Course.objects.all().order_by('-created_at')
    return render(request, 'courses/course_list.html', {'courses': courses})

@login_required
@user_passes_test(lambda u: u.role == User.STUDENT)
def enroll_in_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )
    # **Pass only the ID**, not the model or any attributes
    notify_new_enrollment.delay(enrollment.id)
    return redirect('home')


@login_required
@user_passes_test(is_teacher)
def material_upload(request, course_id):
    course = get_object_or_404(Course, pk=course_id, instructor=request.user)
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course
            material.save()
            notify_new_material.delay(material.id)

            return redirect('home')
    else:
        form = MaterialForm()
    return render(request, 'courses/material_form.html', {'form': form, 'course': course})

@login_required
@user_passes_test(lambda u: u.role == User.STUDENT)
def give_feedback(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.course = course
            fb.student = request.user
            fb.save()
            notify_new_feedback.delay(fb.id)

            return redirect('home')
    else:
        form = FeedbackForm()
    return render(request, 'courses/feedback_form.html', {'form': form, 'course': course})



@login_required
def dashboard_view(request):
    status_form = StatusUpdateForm()
    if request.user.role == User.TEACHER:
        courses = Course.objects.filter(instructor=request.user)
        return render(request, 'dashboard/teacher_dashboard.html', {
            'courses': courses,
            'status_form': status_form,
        })
    else:
        enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
        enrolled_ids = [e.course.pk for e in enrollments]
        available_courses = Course.objects.exclude(pk__in=enrolled_ids)
        return render(request, 'dashboard/student_dashboard.html', {
            'enrollments': enrollments,
            'available_courses': available_courses,
            'status_form': status_form,
        })

@login_required
def post_status(request):
    if request.method == 'POST':
        form = StatusUpdateForm(request.POST)
        if form.is_valid():
            su = form.save(commit=False)
            su.user = request.user
            su.save()
    return redirect('home')
