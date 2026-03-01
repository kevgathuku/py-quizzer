from django import forms


class AnswerForm(forms.Form):
    answer_id = forms.IntegerField(widget=forms.RadioSelect, required=True)
