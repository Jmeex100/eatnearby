from django.core.management.base import BaseCommand
from payments.models import PaymentHistory
import uuid

class Command(BaseCommand):
    help = 'Populate transaction_id for PaymentHistory records with null or empty values'

    def handle(self, *args, **kwargs):
        updated_count = 0
        for payment in PaymentHistory.objects.filter(
            transaction_id__isnull=True
        ) | PaymentHistory.objects.filter(transaction_id=''):
            if payment.delivery_info and payment.delivery_info.payment_method != 'cash':
                payment.transaction_id = f"txn_{uuid.uuid4().hex[:10]}"  # Generate short unique ID
                payment.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'Updated payment {payment.id} with transaction_id {payment.transaction_id}'))
            else:
                self.stdout.write(self.style.WARNING(f'Skipped payment {payment.id}: Cash payment or no delivery_info'))
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} payment records'))