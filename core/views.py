from pydoc import locate
import subprocess
import json
import os
from datetime import date, timedelta
from django.utils.dateparse import parse_date
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Alert

@api_view(['GET'])
def hello_world(request):
    return Response({
        "message": "Hello World!",
        "status": "success"
    })

@api_view(["GET"])
def get_alerts(request):
    # filtering logic
    # id: if provided -> returns only that one (or empty)
    # from/to: filter by date within range
    # disease/species/region: match if alert has ANY of the requested values
    # location: match if ANY requested location term appears in ANY location path

    # read the params (optional for users)

    alert_id = request.query_params.get("id")
    from_date = request.query_params.get("from")
    to_date = request.query_params.get("to")
    diseases = request.query_params.getlist("disease")
    species = request.query_params.getlist("species")
    regions = request.query_params.getlist("region")
    locations = request.query_params.getlist("location")


    # default behaviour
    # if from/to not provided -> last 1 year

    today = date.today()

    if not from_date and not to_date:
        from_date = today - timedelta(days=365)
        to_date = today
    else:
        if from_date:
            from_date = parse_date(from_date)
        if to_date:
            to_date = parse_date(to_date)

    # retrieves all alerts from database
    query_set = Alert.objects.all().order_by("-date")

    # ID filter
    if alert_id:
        query_set = query_set.filter(external_id=alert_id)

    # Date filter
    if from_date:
        query_set = query_set.filter(date__gte=from_date)

    if to_date:
        query_set = query_set.filter(date__lte=to_date)


    # Disease filter
    if diseases:
        for d in diseases:
            query_set = query_set.filter(diseases__icontains=d)

    # Species filter
    if species:
        for s in species:
            query_set = query_set.filter(species__icontains=s)

    # Region filter
    if regions:
        for r in regions:
            query_set = query_set.filter(regions__icontains=r)

    # Location filter
    if locations:
        location_query = Q()

        for loc in locations:
            location_query |= Q(locations__icontains=loc)

        query_set = query_set.filter(location_query)

    def serialise(alert):
        return {
            "id": alert.external_id,
            "date": alert.date.isoformat(),
            "title": alert.title,
            "disease": alert.diseases,
            "species": alert.species,
            "region": alert.regions,
            "location": alert.locations
        }

    alerts_out = [serialise(alert) for alert in query_set]
    return Response({"alerts": alerts_out}, status=status.HTTP_200_OK)

@api_view(['GET'])
def simple_scrapy_test(request):
    # locate the scraper directory
    scraper_path = os.path.join(os.getcwd(), 'scraper')

    try:
        # run Scrapy spider and capture output
        output = subprocess.check_output(
            [
                'scrapy', 'crawl', 'test', # run the 'promed' name spider
                '--nolog',           # close the log output
                '-o', '-:json'       # output to stdout in JSON format
            ],
            cwd=scraper_path,
            stderr=subprocess.STDOUT
        )

        data = json.loads(output)
        return Response(data)

    except subprocess.CalledProcessError as e:
        return Response({
            "error": "Scrapy failed",
            "detail": e.output.decode()
        }, status=500)