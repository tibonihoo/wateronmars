from datetime import timedelta


class FeedStatus:

    STATUS_PARSING_EXCEPTION = 26342
    GRACE_PERIOD = timedelta(weeks=4)

    def __init__(self, *, is_broken, diagnostic = None):
        self.is_broken = is_broken
        self.diagnostic = diagnostic

    @staticmethod
    def check_and_record(feed, status, actual_href, status_date):

        if status < 400:
            if status==301:
                feed.xmlURL = actual_href
                feed.save()
            if feed.last_update_failed:
                feed.last_update_failed = False
                feed.save()
            return FeedStatus(is_broken=False)

        if not feed.last_update_failed:
            feed.latest_update_failure_start_date = status_date

        if status == 410: # Gone
            diagnostic = f"Feed declared as Gone (Status {status})"
            feed.set_permanent_failure(diagnostic, status_date)
        else:
            diagnostic = "Parse Error" if status == FeedStatus.STATUS_PARSING_EXCEPTION else f"Status {status}"
            duration_of_consecutive_failures = (status_date - feed.latest_update_failure_start_date)
            if feed.last_update_failed and duration_of_consecutive_failures > FeedStatus.GRACE_PERIOD:
                diagnostic = f"Feed update failed after consistently failing since {duration_of_consecutive_failures} ({diagnostic})"
                feed.set_permanent_failure(diagnostic, status_date)

        feed.last_update_failed = True
        feed.save()
        return FeedStatus(is_broken=True, diagnostic=diagnostic)
