import time
from datetime import datetime


class Job:

    def __init__(self, hour, minute, func):
        self.hour = hour
        self.minute = minute
        self.func = func
        self.last_run = None


class CronScheduler:

    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def start(self):

        print("Scheduler Started...")

        while True:

            now = datetime.now()

            for job in self.jobs:

                if now.hour == job.hour and now.minute == job.minute:

                    current = now.strftime("%Y-%m-%d %H:%M")

                    if job.last_run != current:

                        job.func()

                        job.last_run = current

            time.sleep(1)