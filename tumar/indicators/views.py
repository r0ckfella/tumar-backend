from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from tumar.animals.models import Cadastre

from .exceptions import (
    ImageryRequestAlreadyExistsError,
    FreeRequestsExpiredError,
    CadastreNotInEgisticError,
)
from .models import ImageryRequest

# Create your views here.


class RequestIndicatorsView(APIView):
    def post(self, request):
        if "cadastre_id" not in request.data:
            return Response(
                {"error": "Provide cadastre id"}, status=status.HTTP_404_NOT_FOUND
            )

        the_cadastre = get_object_or_404(
            Cadastre, pk=request.data["cadastre_id"], farm__user=request.user
        )

        ir = None
        try:
            ir = ImageryRequest(cadastre=the_cadastre)
            if "requested_date" in request.data:
                ir.requested_date = request.data["requested_date"]
            ir.save()
        except ImageryRequestAlreadyExistsError:
            Response(
                {
                    "error": (
                        "Imagery Request for this requested date {} already exists."
                    ).format(ir.requested_date)
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            ir.start_image_processing()
        except FreeRequestsExpiredError:
            Response(
                {"error": "You used all free requests for image processing."},
                status=status.HTTP_409_CONFLICT,
            )
        except CadastreNotInEgisticError:
            Response(
                {
                    "error": (
                        "This cadastre with cad_number {}" " is not in egistic db"
                    ).format(the_cadastre.cad_number)
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {"imageryrequest_id": ir.pk, "requested_date": ir.requested_date},
            status=status.HTTP_201_CREATED,
        )


class LatestIndicatorsView(APIView):
    def get(self, request, cadastre_id):
        the_cadastre = get_object_or_404(
            Cadastre, farm__user=request.user, pk=cadastre_id
        )
        response_data = []

        qs = ImageryRequest.objects.filter(cadastre=the_cadastre).order_by(
            "-requested_date"
        )

        for ir in qs:
            response_data.append(
                dict(
                    id=ir.id,
                    requested_date=ir.requested_date,
                    created_at=ir.created_at,
                    status=ir.status,
                    finished_at=ir.finished_at,
                    results_dir=ir.results_dir,
                    is_layer_created=ir.is_layer_created,
                    ndvi=ir.ndvi,
                    gndvi=ir.gndvi,
                    clgreen=ir.clgreen,
                    ndmi=ir.ndmi,
                    ndsi=ir.ndsi,
                    ndvi_dir=ir.ndvi_dir,
                    gndvi_dir=ir.gndvi_dir,
                    clgreen_dir=ir.clgreen_dir,
                    ndmi_dir=ir.ndmi_dir,
                    rgb_dir=ir.rgb_dir,
                )
            )

        return Response(response_data, status=status.HTTP_200_OK)
