from rest_framework.views import APIView, Request, Response, status
from .models import Pet
from .serializers import PetSerializer
from groups.models import Group
from traits.models import Trait
from rest_framework.pagination import PageNumberPagination
import ipdb
from django.shortcuts import get_object_or_404


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        pets = Pet.objects.all()
        trait_param = request.query_params.get("trait")
        if trait_param:
            trait = get_object_or_404(Trait, name=trait_param)
            print(trait.pets.all())
            pets = trait.pets.all()

        result_page = self.paginate_queryset(pets, request, view=self)
        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group_data = serializer.validated_data.pop("group")
        traits_data = serializer.validated_data.pop("traits")
        group = Group.objects.filter(
            scientific_name__iexact=group_data["scientific_name"]
        ).first()

        if not group:
            group = Group.objects.create(**group_data)
        pet = Pet.objects.create(**serializer.validated_data, group=group)

        for trait_data in traits_data:
            trait = Trait.objects.filter(
                name__iexact=trait_data["name"],
            ).first()

            if not trait:
                trait = Trait.objects.create(**trait_data)

            pet.traits.add(trait)

        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_201_CREATED)


class PetDetailView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(pet)

        return Response(serializer.data)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        group_data: dict = serializer.validated_data.pop("group", None)
        traits_data = serializer.validated_data.pop("traits", None)
        if group_data:
            group = Group.objects.filter(
                scientific_name__iexact=group_data["scientific_name"]
            ).first()
            if not group:
                group = Group.objects.create(**group_data)

            pet.group = group
            pet.save()
            print(vars(pet.group))

        if traits_data:

            for trait_data in traits_data:
                trait = Trait.objects.filter(
                    name__iexact=trait_data["name"],
                ).first()

            if not trait:
                trait = Trait.objects.create(**trait_data)

            pet.traits.add(trait)

        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)

        pet.save()

        serializer = PetSerializer(pet)
        return Response(serializer.data)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        pet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
