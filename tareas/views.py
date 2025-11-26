from django.shortcuts import render
from django.views.generic import DetailView
from .models import Task
# Create your views here.
class detalle_tarea(DetailView):
    model = Task
    template_name = 'detalle_tarea.html'