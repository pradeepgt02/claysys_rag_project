from collections import deque
from app.crawler.url_normalizer import normalize_crawl_url

class CrawlQueue:
    """
    A FIFO queue implementation for managing URLs to crawl.
    Uses collections.deque and an internal set to ensure duplicate URLs
    are not added to the queue.
    """
    def __init__(self):
        self._queue = deque()
        self._seen = set()

    def add(self, url: str) -> bool:
        """
        Adds a URL to the queue if it has not been added previously.
        Normalizes the URL before checking and adding.
        Returns True if added, False if it was a duplicate.
        """
        normalized_url = normalize_crawl_url(url)
        if not normalized_url:
            return False

        if normalized_url not in self._seen:
            self._seen.add(normalized_url)
            self._queue.append(normalized_url)
            return True
        return False


    def pop(self) -> str:
        """
        Removes and returns the next URL to crawl (FIFO).
        Raises IndexError if the queue is empty.
        """
        return self._queue.popleft()

    def is_empty(self) -> bool:
        """
        Returns True if the queue is empty, False otherwise.
        """
        return len(self._queue) == 0

    def size(self) -> int:
        """
        Returns the number of items currently in the queue.
        """
        return len(self._queue)
