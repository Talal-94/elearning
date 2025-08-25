from django.contrib.auth import get_user_model
from rest_framework import serializers
from courses.models import Course, Enrollment, Material, Feedback

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "role", "date_joined"]

class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "description", "instructor", "created_at"]
        read_only_fields = ["instructor", "created_at"]

class EnrollmentSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "course", "enrolled_at"]
        read_only_fields = ["student", "enrolled_at"]

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ["id", "course", "title", "upload", "uploaded_at"]
        read_only_fields = ["uploaded_at"]

class FeedbackSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)

    class Meta:
        model = Feedback
        fields = ["id", "student", "course", "content", "created_at"]
        read_only_fields = ["student", "created_at"]
