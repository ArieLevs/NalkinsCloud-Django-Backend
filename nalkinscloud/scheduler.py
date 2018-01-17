from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from nalkinscloud.functions import generate_random_16_digit_string
from django.conf import settings
# from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

import logging
import datetime

from pytz import utc

now = datetime.datetime.now()

# Since we use 'apscheduler' The first weekday is always monday.
days_to_ints = {'Sunday': '6', 'Monday': '0', 'Tuesday': '1',
                'Wednesday': '2', 'Thursday': '3', 'Friday': '4', 'Saturday': '5'}
'''
jobstores = {
    'mongo': {'type': 'mongodb'},
    # 'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}'''

executors = {
    'default': {'type': 'threadpool', 'max_workers': 20},
    'processpool': ProcessPoolExecutor(max_workers=5)
}

job_defaults = {
    'coalesce': False,
    'max_instances': 3
}
scheduler = BackgroundScheduler()

scheduler.configure(executors=executors, job_defaults=job_defaults, timezone=utc)
# scheduler.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)

scheduler.start()


# define the function that is to be executed
def execute_scheduled_job(topic, payload):
    # publish_message(topic, payload)
    print(topic)
    print(payload)


def schedule_new_job(device_id,
                     topic,
                     is_repeated_job,
                     repeated_days_array,
                     job_action,
                     end_date_time_selected,
                     utc_start_date,
                     utc_end_date):
    logging.basicConfig(filename=settings.BASE_DIR + '/logs/scheduled_job.log', level=logging.DEBUG)
    logging.info(now)
    logging.info('Started function "do_scheduled_job"')
    logging.info('Device id: ' + device_id)
    logging.info('Topic: ' + topic)
    # Understand what should be sent when time arrived,
    # if job_action True then send 1, else send 0 as the message payload
    if job_action:
        message_payload = '1'
    else:
        message_payload = '0'
    logging.info('message_payload: ' + message_payload)

    # Generate random id for the job, its build from the device id + random 16 character long string
    job_id = device_id + generate_random_16_digit_string()

    # If user selected repeated job, a cron like scheduler should run
    if is_repeated_job:
        logging.info('Setting scheduled job with cron (repeated)')
        # If user selected an end date then do
        if end_date_time_selected:
            # Use 'cron' trigger, and use start, and end date
            scheduler.add_job(execute_scheduled_job, 'cron', id=job_id,
                              day_of_week=return_days_from_dict(repeated_days_array),
                              start_date=utc_start_date,
                              end_date=utc_end_date,
                              replace_existing=True,
                              args=[topic, message_payload])
        # If user did not marked end date then do
        else:
            # Use 'cron' trigger, use start date only
            scheduler.add_job(execute_scheduled_job, 'cron', id=job_id,
                              day_of_week=return_days_from_dict(repeated_days_array),
                              start_date=utc_start_date,
                              replace_existing=True,
                              args=[topic, message_payload])

    # If a 'single time' job requested then
    else:  # Then there can be 2 options, with end time or not
        logging.info('Setting scheduled job with date (one time run)')
        if end_date_time_selected:
            # Use 'date' trigger, that means run once
            # Run function with end date
            scheduler.add_job(execute_scheduled_job, 'date', id=job_id,
                              start_date=utc_start_date,
                              end_date=utc_end_date,
                              replace_existing=True, args=[topic, message_payload])
        else:
            # Use 'date' trigger, that means run once
            # Run function only with start date
            scheduler.add_job(execute_scheduled_job, 'date', id=job_id,
                              run_date=utc_start_date,
                              replace_existing=True, args=[topic, message_payload])

    return job_id


# Param - receives a String
# Kills the job with an equal id
def remove_job_by_id(job_id):
    logging.basicConfig(filename=settings.BASE_DIR + '/logs/scheduled_job.log', level=logging.DEBUG)
    logging.info(now)
    logging.info('Started function "remove_job_by_id"')
    scheduler.remove_job(job_id)


# Function will receive a dictionary, and return a string
# Param example:
# {'Sunday': False, 'Monday': True, 'Tuesday': False,
#  'Wednesday': False, 'Thursday': True, 'Friday': False, 'Saturday': False}
def return_days_from_dict(days_to_repeat):
    logging.basicConfig(filename=settings.BASE_DIR + '/logs/scheduled_job.log', level=logging.DEBUG)
    logging.info(now)
    logging.info('Started function "return_days_from_dict"')
    result = ''
    # Iterate on the input dict, and on the hard coded 'days_to_ints' dict
    for (key, value), (key2, value2) in days_to_repeat.items(), days_to_ints.items():
        if value:  # If current value equals True, then this day was selected for repeated job
            result += value2  # Append the 'True' day to the result
    return result
