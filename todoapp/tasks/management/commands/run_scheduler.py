from django.core.management.base import BaseCommand

from tasks.scheduler import CronScheduler, Job
from tasks.jobs import send_email


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        scheduler = CronScheduler()

        scheduler.add_job(
            Job(10, 11, send_email)
        )

        scheduler.start()