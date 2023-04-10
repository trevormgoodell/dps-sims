import heapq

class Priority_Queue:
    def __init__(self):
        self.queue = []

    def append(self, item):
        heapq.heappush(self.queue, item)

    def pop(self, index):
        return self.queue.pop(index)
    
    def __contains__(self, item):
        return item in [i[1] for i in self.queue]