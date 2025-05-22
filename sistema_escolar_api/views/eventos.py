from django.shortcuts import render
from django.db.models import *
from django.db import transaction
from sistema_escolar_api.serializers import *
from sistema_escolar_api.models import *
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.generics import CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from django.core import serializers
from django.utils.html import strip_tags
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from rest_framework.permissions import AllowAny
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string

import string
import random
import json

class EventosAll(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        eventos = Evento.objects.all().order_by("id")
        serializer = EventoSerializer(eventos, many=True)
        return Response(serializer.data, status=200)
    

class EventoView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='administrador').exists():
            return Response({"detail": "No tienes permisos para ver eventos."}, status=status.HTTP_403_FORBIDDEN)

        evento_id = request.GET.get("id")
        if not evento_id:
            return Response({"detail": "ID del evento no proporcionado"}, status=status.HTTP_400_BAD_REQUEST)

        evento = get_object_or_404(Evento, id=evento_id)
        serializer = EventoSerializer(evento)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def get(self, request, *args, **kwargs):
        if request.user.groups.filter(name='administrador').exists():
            evento_id = request.GET.get("id")
            if evento_id:
                evento = get_object_or_404(Evento, id=evento_id)
                serializer = EventoSerializer(evento)
                return Response(serializer.data, status=status.HTTP_200_OK)

            
            eventos = Evento.objects.all().order_by("id")
            serializer = EventoSerializer(eventos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        grupo = request.user.groups.first()
        if not grupo:
            return Response({"detail": "No tienes asignado un rol válido."}, status=status.HTTP_403_FORBIDDEN)

        rol = grupo.name.lower()
        if rol == 'maestro':
            eventos = Evento.objects.filter(publico_objetivo__in=['Profesores', 'Público general'])
        elif rol == 'alumno':
            eventos = Evento.objects.filter(publico_objetivo__in=['Estudiantes', 'Público general'])
        else:
            return Response({"detail": "Rol no válido."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = EventoSerializer(eventos.order_by("id"), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Crear evento
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='administrador').exists():
            return Response({"detail": "No tienes permisos para crear eventos."}, status=status.HTTP_403_FORBIDDEN)

        serializer = EventoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Editar evento
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='administrador').exists():
            return Response({"detail": "No tienes permisos para editar eventos."}, status=status.HTTP_403_FORBIDDEN)

        evento = get_object_or_404(Evento, id=request.data.get("id"))
        serializer = EventoSerializer(evento, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Eliminar evento
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='administrador').exists():
            return Response({"detail": "No tienes permisos para eliminar eventos."}, status=status.HTTP_403_FORBIDDEN)

        evento = get_object_or_404(Evento, id=request.GET.get("id"))
        evento.delete()
        return Response({"detail": "Evento eliminado correctamente."}, status=status.HTTP_200_OK)

    