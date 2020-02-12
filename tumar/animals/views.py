import datetime

import django.utils.timezone as tz

from django.contrib.gis.geos import Point, Polygon, GEOSGeometry
from django.contrib.gis.measure import Distance as d
from django.contrib.gis.db.models import Extent
from django.db import connections
from django.db.models import Max
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from geopy.geocoders import GeoNames
from rest_framework import viewsets, status, mixins
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from . import utils
from .filters import AnimalPathFilter, AnimalNameOrTagNumberFilter
from .models import Farm, Animal, Geolocation, Machinery, Event, Cadastre
from .serializers import FarmSerializer, GeolocationAnimalSerializer, EventAnimalSerializer, AnimalSerializer, \
    MachinerySerializer, CadastreSerializer, FarmCadastresSerializer, CreateFarmSerializer


# Create your views here.

class FarmViewSet(viewsets.ModelViewSet):
    """
    Lists, retrieves, creates, and deletes farms
    """
    queryset = Farm.objects.all().order_by('iin')
    model = Farm

    def get_serializer_class(self):
        serializers_class_map = {
            'default': FarmCadastresSerializer,
            'create': CreateFarmSerializer,
        }
        return serializers_class_map.get(self.action, serializers_class_map['default'])


class CadastreFarmViewSet(viewsets.ModelViewSet):
    """
    Lists, retrieves, creates, and deletes cadastres and their farm
    """
    queryset = Cadastre.objects.all().order_by('id')
    serializer_class = CadastreSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('cad_number', '')


class AnimalFarmViewSet(viewsets.ModelViewSet):
    """
    Lists, retrieves, creates, and deletes animals and their farm
    """
    # queryset = Animal.objects.all().order_by('imei')
    serializer_class = AnimalSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = AnimalNameOrTagNumberFilter

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Animal.objects.all()
        return Animal.objects.filter(farm__user=self.request.user)


class MachineryFarmViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lists and retrieves machinery and their farm
    """
    queryset = Machinery.objects.all().order_by('machinery_code')
    serializer_class = MachinerySerializer


class GeolocationAnimalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lists and retrieves geolocations and their animal
    """
    queryset = Geolocation.geolocations.all().order_by('animal__imei', '-time')
    serializer_class = GeolocationAnimalSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('animal__imei', 'time',)


class EventAnimalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lists and retrieves events and their animal
    """
    queryset = Event.objects.all().order_by('animal__imei', '-time')
    serializer_class = EventAnimalSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('animal__imei',)


class MyFarmView(APIView):
    def get(self, request):
        my_farm = get_object_or_404(Farm, user=self.request.user)
        serializer = FarmCadastresSerializer(my_farm)

        return Response(serializer.data)


class SearchCadastreView(APIView):
    """
    Search cadastres by cadastre number in Kazakhstan Cadastre Database

        url: api/v1/cadastres/search-cadastre/?cad_number=01011008053
        input: cad_number
        output: PK, cad_number, geometry, nearest town
    """

    def get(self, request):
        data = {'pk': None, 'cad_number': request.query_params.get('cad_number'), 'geom': None,
                'nearest_town': None}

        with connections['egistic_2'].cursor() as cursor:
            cursor.execute(
                "SELECT id, ST_AsText(ST_Transform(geom, 3857)) FROM cadastres_cadastre WHERE kad_nomer = %s",
                [data.get('cad_number')])
            row = cursor.fetchone()
            data['pk'] = row[0]
            data['geom'] = row[1]

        # find nearby town
        cadastre = GEOSGeometry(data['geom'], srid=3857)
        data['geom'] = cadastre.geojson

        cad_point = cadastre.point_on_surface
        cad_point.transform(4326)
        coords = tuple(cad_point.coord_seq)
        coords = [coords[0][1], coords[0][0]]  # swapping lon and lat
        geolocator = GeoNames(user_agent="zest88", username='zest88')
        nearest_town = geolocator.reverse(coords, find_nearby_type='findNearby', exactly_one=False)
        data['nearest_town'] = str(nearest_town[0])
        return Response(data)


class GetAnimalPathView(APIView):
    """
    View to get the path of an animal between two dates (time included).
    """

    def get(self, request):
        """
        Return a Linestring(GeoJSON) of the path.

        url example: {baseURL}/api/v1/get-path/?imei=869270046995022&time_before=2019-12-03 00:00:00
        """
        valid_query_params = ('imei', 'time_after', 'time_before',)
        queryset = Geolocation.geolocations.all().order_by('time')

        if not request.GET or not all(param in valid_query_params for param in tuple(request.query_params.keys())):
            return Response({"valid query params": valid_query_params}, status=status.HTTP_404_NOT_FOUND)

        filtered_data = AnimalPathFilter(request.GET, queryset=queryset)

        if filtered_data.qs.count() > 1:
            geometry = utils.get_linestring_from_geolocations(filtered_data.qs)
        else:
            modified_get = request.GET.copy()
            if 'time_after' not in modified_get and filtered_data.qs.count() < 2:
                raise NotFound(detail=_('Not enough geolocations to construct LineString'))

            modified_get.pop('time_after')
            filtered_data = AnimalPathFilter(modified_get, queryset=queryset)
            geometry = utils.get_linestring_from_geolocations(filtered_data.qs[filtered_data.qs.count()-2:])

        return Response(geometry.geojson)  # Any Python primitive is ok, linestring.geojson is str fyi


class SimpleGroupedGeolocationsView(APIView):
    """
    View to return latest geolocation for each animal of the farm
    """
    zoom_distance = {11: (30, 7), 12: (20, 4), 13: (10, 2), 14: (5, 0),
                     0: (0, 40)}  # (initial query radius, distance bw geolocs)
    valid_query_params = ('lon', 'lat', 'zoom',)

    def get(self, request):

        if not all(param in self.valid_query_params for param in tuple(request.query_params.keys())):
            return Response({"valid query params": self.valid_query_params}, status=status.HTTP_404_NOT_FOUND)

        the_farm = get_object_or_404(Farm, user=request.user)
        # animal_pks = the_farm.animals.values_list('pk', flat=True)
        response_json = {"animals": [], "groups": []}

        # center_lon = request.query_params.get('lon')
        # center_lat = request.query_params.get('lat')
        zoom_level = request.query_params.get('zoom')

        if zoom_level is None or int(zoom_level) < 11:
            zoom_level = 11

        qs = Geolocation.geolocations.filter(animal__farm=the_farm).order_by('animal__id', '-time') \
            .distinct('animal__id')  # latest for each group

        if int(zoom_level) >= 14:  # list(self.zoom_distance.keys())[-1]:  closest zoom returns all geolocations
            serializer = GeolocationAnimalSerializer(qs, many=True)
            response_json["animals"] = serializer.data
        else:
            groups = utils.cluster_geolocations(qs.values_list('pk', flat=True), self.zoom_distance, zoom_level)

            for group in groups:
                if len(group) != 1:
                    temp_group_qs = Geolocation.geolocations.filter(pk__in=group)
                    latest_geoloc_time = temp_group_qs.filter(time__isnull=False).latest('time').time
                    group_center_point_bbox = temp_group_qs.aggregate(Extent('position'))
                    group_center_point = Polygon.from_bbox(group_center_point_bbox['position__extent']).centroid
                    temp_group_data = {"position": group_center_point.json, 'time': latest_geoloc_time,
                                       'animals_num': len(group)}
                    response_json["groups"].append(temp_group_data)
                else:
                    single_animal = Geolocation.geolocations.get(pk=group.pop())
                    serializer = GeolocationAnimalSerializer(single_animal)
                    response_json["animals"].append(serializer.data)

        return Response(response_json)


class LatestGroupedGeolocationsView(APIView):
    """
    View to return groups of points that are near to each other and single lone points. This is based on
    4 zoom levels.
    """
    zoom_distance = {11: (30, 7), 12: (20, 4), 13: (10, 2), 14: (5, 0),
                     0: (0, 40)}  # (initial query radius, distance bw geolocs)
    valid_query_params = ('lon', 'lat', 'zoom',)

    def get(self, request):

        if not all(param in self.valid_query_params for param in tuple(request.query_params.keys())):
            return Response({"valid query params": self.valid_query_params}, status=status.HTTP_404_NOT_FOUND)

        the_farm = get_object_or_404(Farm, user=request.user)
        animal_pks = the_farm.animals.values_list('pk', flat=True)
        response_json = {"animals": [], "groups": []}

        if not request.GET:
            """
            Find most populated group
            """
            qs = Geolocation.geolocations.filter(animal__in=animal_pks,
                                                 time=datetime.datetime(2019, 12, 30, 4, 0, 0))
                                                 # time__range=(tz.now() - tz.timedelta(hours=1), tz.now()))
            zoom_level = 0
        else:
            center_lon = request.query_params.get('lon')
            center_lat = request.query_params.get('lat')
            zoom_level = request.query_params.get('zoom')

            qs = Geolocation.geolocations.filter(animal__in=animal_pks,
                                                 time=datetime.datetime(2019, 12, 30, 4, 0, 0),
                                                 # time__range=(tz.now() - tz.timedelta(hours=1), tz.now()),
                                                 position__dwithin=(
                                                     Point(float(center_lon), float(center_lat), srid=3857),
                                                     d(km=self.zoom_distance[int(zoom_level)][
                                                         0]))).order_by('pk')

            if zoom_level == list(self.zoom_distance.keys())[-1]:  # closest zoom returns all geolocations
                serializer = GeolocationAnimalSerializer(qs, many=True)
                response_json["animals"] = serializer.data["results"]
                return Response(response_json)

        groups = utils.cluster_geolocations(qs, self.zoom_distance, zoom_level)

        if not request.GET:
            groups.sort(key=len, reverse=True)
            biggest_group_count = len(groups[0])
            biggest_group_qs = Geolocation.geolocations.filter(pk__in=groups[0])
            groups = utils.cluster_geolocations(biggest_group_qs, self.zoom_distance,
                                                next(iter(self.zoom_distance.keys())))
            assert len([item for group in groups for item in group]) == biggest_group_count, (
                "PKs must be unique across"
                " every element in every group.")

        # print("Total animal count: {}, with zoom level: {}".format(len([item for group in groups for item in group]),
        #       zoom_level))

        for group in groups:
            if len(group) != 1:
                temp_group_qs = Geolocation.geolocations.filter(pk__in=group)
                latest_geoloc_time = temp_group_qs.filter(time__isnull=False).latest('time').time
                group_center_point_bbox = temp_group_qs.aggregate(Extent('position'))
                group_center_point = Polygon.from_bbox(group_center_point_bbox['position__extent']).centroid
                temp_group_data = {"position": group_center_point.json, 'time': latest_geoloc_time,
                                   'animals_num': len(group)}
                response_json["groups"].append(temp_group_data)
            else:
                single_animal = Geolocation.geolocations.get(pk=group.pop())
                serializer = GeolocationAnimalSerializer(single_animal)
                response_json["animals"].append(serializer.data)

        return Response(response_json)
