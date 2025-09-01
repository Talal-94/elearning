import os
from django import forms
from .models import Course, Feedback, Material, StatusUpdate

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["title", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["title", "upload"]

    def clean_upload(self):
        f = self.cleaned_data.get("upload")
        if not f:
            return f

        # Allowed extensions & size cap 10 MB
        allowed_exts = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".zip"}
        max_size = 10 * 1024 * 1024 

        ext = os.path.splitext(f.name)[1].lower()
        if ext not in allowed_exts:
            raise forms.ValidationError(
                "Unsupported file type. Allowed: pdf, doc, docx, ppt, pptx, zip."
            )
        if getattr(f, "size", 0) > max_size:
            raise forms.ValidationError("File too large (max 10 MB).")

        return f


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["content"]
        widgets = {"content": forms.Textarea(attrs={"rows": 3})}


class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = StatusUpdate
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 2, "placeholder": "What’s on your mind?"}
            )
        }
