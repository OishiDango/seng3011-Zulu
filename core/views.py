import subprocess
import json
import os

from collections import Counter
from django.db.models import Count
from datetime import date, timedelta

from django.db.models import Q
from django.utils.dateparse import parse_date
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth

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

    if to_date:
        to_date = parse_date(to_date)
    else:
        to_date = today

    if from_date:
        from_date = parse_date(from_date)
    else:
        from_date = to_date - timedelta(days=default_days)

    query_set = Alert.objects.all().order_by("-date")

    if alert_id:
        query_set = query_set.filter(external_id=alert_id)

    if from_date:
        query_set = query_set.filter(date__gte=from_date)

    if to_date:
        query_set = query_set.filter(date__lte=to_date)

    if diseases:
        disease_query = Q()
        for d in diseases:
            disease_query |= Q(diseases__icontains=d)
        query_set = query_set.filter(disease_query)

    if species:
        species_query = Q()
        for s in species:
            species_query |= Q(species__icontains=s)
        query_set = query_set.filter(species_query)

    if regions:
        region_query = Q()
        for r in regions:
            region_query |= Q(regions__icontains=r)
        query_set = query_set.filter(region_query)

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
    query_set, from_date, to_date = filter_alerts(
        request.query_params,
        default_days=30,
    )

    requested_regions = request.query_params.getlist("region")
    requested_regions_lower = {r.lower() for r in requested_regions if r}

    region_counter = Counter()

    for alert in query_set:
        for region in alert.regions or []:
            if not region:
                continue

            if requested_regions_lower:
                if region.lower() in requested_regions_lower:
                    region_counter[region] += 1
            else:
                region_counter[region] += 1

    by_region = [
        {"region": region, "count": count}
        for region, count in sorted(
            region_counter.items(),
            key=lambda x: (-x[1], x[0]),
        )
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
    query_set, from_date, to_date = filter_alerts(
        request.query_params,
        default_days=30,
    )

    requested_diseases = request.query_params.getlist("disease")
    requested_diseases_lower = {d.lower() for d in requested_diseases if d}

    disease_counter = Counter()

    for alert in query_set:
        for disease in alert.diseases or []:
            if not disease:
                continue

            if requested_diseases_lower:
                if disease.lower() in requested_diseases_lower:
                    disease_counter[disease] += 1
            else:
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
            "from": from_date.isoformat() if from_date else None,
            "to": to_date.isoformat() if to_date else None,
            "alerts": alerts_out,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def stats_timeseries(request):
    interval = request.query_params.get("interval", "day")

    trunc_map = {
        "day": TruncDay,
        "week": TruncWeek,
        "month": TruncMonth,
    }

    if interval not in trunc_map:
        return Response(
            {"error": "Invalid interval"},
            status=status.HTTP_400_BAD_REQUEST
        )

    queryset, from_date, to_date = filter_alerts(
        request.query_params,
        default_days=90
    )

    trunc_func = trunc_map[interval]

    series = (
        queryset
        .annotate(period=trunc_func("date"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    results = [
        {
            "period": row["period"].isoformat(),
            "count": row["count"]
        }
        for row in series
    ]

    return Response(
        {
            "interval": interval,
            "from": from_date.isoformat() if from_date else None,
            "to": to_date.isoformat() if to_date else None,
            "results": results,
        },
        status=status.HTTP_200_OK
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
