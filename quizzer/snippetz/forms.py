from django import forms


class AnswerForm(forms.Form):
    version_id = forms.IntegerField(widget=forms.RadioSelect, required=True)
