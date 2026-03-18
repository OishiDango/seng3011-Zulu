import json
from pathlib import Path

from django.core.management.base import BaseCommand
from core.models import Alert


class Command(BaseCommand):
    help = "Import alerts from a Django fixture-style JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="alerts.json",
            help="Path to alerts JSON file",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        batch = []
        created = 0
        skipped = 0

        existing_ids = set(
            Alert.objects.values_list("external_id", flat=True)
        )

        for item in data:
            fields = item.get("fields", {})
            external_id = fields.get("external_id")

            if not external_id or external_id in existing_ids:
                skipped += 1
                continue

            batch.append(
                Alert(
                    external_id=external_id,
                    date=fields.get("date"),
                    title=fields.get("title", ""),
                    diseases=fields.get("diseases", []),
                    species=fields.get("species", []),
                    regions=fields.get("regions", []),
                    locations=fields.get("locations", []),
                )
            )
            existing_ids.add(external_id)

            if len(batch) >= 1000:
                Alert.objects.bulk_create(batch, batch_size=1000)
                created += len(batch)
                self.stdout.write(f"Inserted {created} alerts...")
                batch = []

        if batch:
            Alert.objects.bulk_create(batch, batch_size=1000)
            created += len(batch)

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete. Created: {created}, skipped: {skipped}"
            )
        )