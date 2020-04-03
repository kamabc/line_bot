from apscheduler.schedulers.blocking import BlockingScheduler
import main

twische = BlockingScheduler()

@twische.scheduled_job('interval',minutes=20)
def timed_job():
    main.reset_status()

if __name__ == "__main__":
    twische.start()
