from django.core.management.base import BaseCommand
from merchants.models import Merchant
from profiles.models import ShortURL
import csv


class Command(BaseCommand):
    help = "Back up all vault objects"

    def handle(self, *args, **kwargs):
        HEADERS = ['Name', 'Address', 'Profile Link']
        with open('/tmp/map_data.csv', 'w') as f:
            csv_writer = csv.DictWriter(f, HEADERS)
            csv_writer.writeheader()

            merchants = Merchant.objects.filter(address_1__isnull=False)
            for m in merchants:
                short_url = m.get_short_url()
                if not short_url:
                    short_url = m.create_short_url()
                csv_writer.writerow(
                    {
                        'Name': m.business_name,
                        'Address': m.get_physical_address_qs(),
                        'Profile Link': short_url.get_profile_url()

                    }
                )