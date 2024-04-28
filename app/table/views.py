from django.forms import model_to_dict
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer

from table.models import (
    create_dynamic_model_class,
    get_dynamic_model_by_name,
    get_table_model_attrs_from_fields,
    update_dynamic_model_fields,
    update_table_from_dynamic_model,
)
from table.serializers import TableRowSerializer, TableSerializer, UpdateTableSerializer


@extend_schema(request=TableSerializer)
@api_view(["POST"])
def generate_dynamic_model(request: Request) -> Response:
    serializer = TableSerializer(data=request.data)
    if serializer.is_valid():
        try:
            model_fields = get_table_model_attrs_from_fields(serializer.data["fields"])
            model = create_dynamic_model_class(
                model_name=serializer.data["name"], fields=model_fields
            )
            return Response(
                {"table_name": model.__name__},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=UpdateTableSerializer)
@api_view(["PUT"])
def update_dynamic_model(request: Request, id: str) -> Response:
    model = get_dynamic_model_by_name(id)
    serializer = UpdateTableSerializer(data=request.data)
    if serializer.is_valid():
        update_dynamic_model_fields(
            model, get_table_model_attrs_from_fields(serializer.data["fields"])
        )
        update_table_from_dynamic_model(model)
        return Response(
            status=status.HTTP_200_OK,
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=ListSerializer(child=TableRowSerializer()),
)
@api_view(["POST"])
def add_row(request: Request, id: str) -> Response:
    model = get_dynamic_model_by_name(id)()
    serializer = ListSerializer(child=TableRowSerializer(), data=request.data)
    if serializer.is_valid():
        try:
            for data in serializer.data:
                setattr(model, data["name"], data["value"])
            model.save()
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            data=model_to_dict(model, fields=[field.name for field in model._meta.fields]),
            status=status.HTTP_201_CREATED,
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def list_rows(request: Request, id: str) -> Response:
    model = get_dynamic_model_by_name(id)
    if model:
        rows = model.objects.all()
        return Response(
            [
                model_to_dict(row, fields=[field.name for field in row._meta.fields])
                for row in rows
            ],
            status=status.HTTP_200_OK,
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)