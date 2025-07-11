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
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string
import string
import random
import json

class AlumnosAll(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        alumnos = Alumnos.objects.filter(user__is_active = 1).order_by("id")
        alumnos = AlumnoSerializer(alumnos, many=True).data
        
        return Response(alumnos, 200)
    
class AlumnosView(generics.CreateAPIView):
    #Obtener usuario por ID
    #permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        try:
            alumno_id = request.GET.get("id")
            if not alumno_id:
                return Response({"detail": "Parámetro 'id' requerido"}, status=status.HTTP_400_BAD_REQUEST)

            alumno = get_object_or_404(Alumnos, id=alumno_id)
            alumno_data = AlumnoSerializer(alumno, many=False).data
            alumnos_json_raw = alumno_data.get("alumnos_json")
            if alumnos_json_raw:
                try:
                    alumno_data["alumnos_json"] = json.loads(alumnos_json_raw)
                except Exception as e:
                    alumno_data["alumnos_json"] = {}
                    print("Error al parsear alumnos_json:", e)

            return Response(alumno_data, status=status.HTTP_200_OK)

        except Exception as e:
            print("ERROR en vista AlumnosView.get:", e)
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #Registrar nuevo usuario
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            #Grab user data
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']
            #Valida si existe el usuario o bien el email registrado
            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                return Response({"message":"Username "+email+", is already taken"},400)

            user = User.objects.create( username = email,
                                        email = email,
                                        first_name = first_name,
                                        last_name = last_name,
                                        is_active = 1)


            user.save()
            user.set_password(password)
            user.save()

            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()

            #Create a profile for the user
            alumno = Alumnos.objects.create(user=user,
                                            matricula= request.data["matricula"],
                                            curp= request.data["curp"].upper(),
                                            rfc= request.data["rfc"].upper(),
                                            fecha_nacimiento= request.data["fecha_nacimiento"],
                                            edad= request.data["edad"],
                                            telefono= request.data["telefono"],
                                            ocupacion= request.data["ocupacion"])
            alumno.save()

            return Response({"alumno_created_id": alumno.id }, 201)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AlumnosViewEdit(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    # Editar alumno
    def put(self, request, *args, **kwargs):
        try:
            # Obtener el alumno por ID
            alumno = get_object_or_404(Alumnos, id=request.data["id"])

            # Actualizar los campos del modelo Alumnos
            alumno.matricula = request.data["matricula"]
            alumno.curp = request.data["curp"].upper()
            alumno.rfc = request.data["rfc"].upper()
            alumno.fecha_nacimiento = request.data["fecha_nacimiento"]
            alumno.edad = request.data["edad"]
            alumno.telefono = request.data["telefono"]
            alumno.ocupacion = request.data["ocupacion"]
            alumno.save()

            # Actualizar los campos del modelo User (solo los que sean necesarios)
            user = alumno.user
            user.first_name = request.data["first_name"]
            user.last_name = request.data["last_name"]
            user.email = request.data["email"]
            user.save()

            # Serializar el objeto Alumnos
            alumno_serializer = AlumnoSerializer(alumno, many=False).data
            return Response(alumno_serializer, 200)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        alumnos = get_object_or_404(Alumnos, id=request.GET.get("id"))
        try:
            alumnos.user.delete()
            return Response({"details": "Alumno eliminado"}, 200)
        except Exception as e:
            return Response({"details": "Algo pasó al eliminar"}, 400)
