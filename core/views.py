import subprocess
import json
import os

from collections import Counter
from datetime import date, timedelta

from django.db.models import Q
from django.utils.dateparse import parse_date

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from core.models import Alert


def filter_alerts(params, default_days=365):
    alert_id = params.get("id")
    from_date = params.get("from")
    to_date = params.get("to")
    diseases = params.getlist("disease")
    species = params.getlist("species")
    regions = params.getlist("region")
    locations = params.getlist("location")

    today = date.today()

    raw_from = params.get("from")
    raw_to = params.get("to")

    from_date = parse_date(raw_from) if raw_from else None
    to_date = parse_date(raw_to) if raw_to else None

    if not from_date and not to_date:
        # default window
        from_date = today - timedelta(days=default_days)
        to_date = today

    elif from_date and not to_date:
        # user provided from only
        to_date = today

    elif to_date and not from_date:
        # user provided to only
        from_date = to_date - timedelta(days=default_days)

    query_set = Alert.objects.all().order_by("-date")

    if alert_id:
        query_set = query_set.filter(external_id=alert_id)

    if from_date:
        query_set = query_set.filter(date__gte=from_date)

    if to_date:
        query_set = query_set.filter(date__lte=to_date)

    if diseases:
        for d in diseases:
            query_set = query_set.filter(diseases__icontains=d)

    if species:
        for s in species:
            query_set = query_set.filter(species__icontains=s)

    if regions:
        for r in regions:
            query_set = query_set.filter(regions__icontains=r)

    if locations:
        location_query = Q()
        for loc in locations:
            location_query |= Q(locations__icontains=loc)
        query_set = query_set.filter(location_query)

    return query_set, from_date, to_date


def serialise_alert(alert):
    return {
        "id": alert.external_id,
        "date": alert.date.isoformat(),
        "title": alert.title,
        "disease": alert.diseases,
        "species": alert.species,
        "region": alert.regions,
        "location": alert.locations,
    }


@api_view(["GET"])
def stats_regions(request):
    query_set, from_date, to_date = filter_alerts(request.query_params, default_days=30)

    region_counter = Counter()

    for alert in query_set:
        for region in alert.regions or []:
            if region:
                region_counter[region] += 1

    by_region = [
        {"region": region, "count": count}
        for region, count in sorted(region_counter.items(), key=lambda x: (-x[1], x[0]))
    ]

    return Response(
        {
            "from": from_date.isoformat() if from_date else None,
            "to": to_date.isoformat() if to_date else None,
            "by_region": by_region,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def stats_diseases(request):
    query_set, from_date, to_date = filter_alerts(request.query_params, default_days=30)

    disease_counter = Counter()

    for alert in query_set:
        for disease in alert.diseases or []:
            if disease:
                disease_counter[disease] += 1

    by_disease = [
        {"disease": disease, "count": count}
        for disease, count in sorted(
            disease_counter.items(),
            key=lambda x: (-x[1], x[0]),
        )
    ]

    return Response(
        {
            "from": from_date.isoformat() if from_date else None,
            "to": to_date.isoformat() if to_date else None,
            "by_disease": by_disease,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def hello_world(request):
    return Response({"message": "Hello World!", "status": "success"})


@api_view(["GET"])
def get_alerts(request):
    query_set, from_date, to_date = filter_alerts(request.query_params)

    alerts_out = [serialise_alert(alert) for alert in query_set]

    return Response(
        {
            "alerts": alerts_out,
            "from": from_date.isoformat() if from_date else None,
            "to": to_date.isoformat() if to_date else None,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
def simple_scrapy_test(request):
    scraper_path = os.path.join(os.getcwd(), "scraper")

    try:
        output = subprocess.check_output(
            ["scrapy", "crawl", "example", "--nolog", "-o", "-:json"],
            cwd=scraper_path,
            stderr=subprocess.STDOUT,
        )

        data = json.loads(output)
        return Response(data)

    except subprocess.CalledProcessError as e:
        return Response(
            {"error": "Scrapy failed", "detail": e.output.decode()}, status=500
        )
