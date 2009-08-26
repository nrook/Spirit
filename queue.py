"""
Contains a priority queue.
"""

class PriorityQueue():
    """
    An ordered queue.
    
    Each element in the queue is associated with an integer.  The element
    returned first is the one with the lowest integer.  Note that if an element
    is inserted into the queue with the same priority as an existing element,
    the existing element will be returned first, then the new one.
    """

    def __init__(self):
        self._list = []

    def isEmpty(self):
        return len(self._list) == 0

    def put(self, item, priority):
        """
        Put an item of priority 'priority' into the queue.
        """

        for i in range(len(self._list)):
            if priority < self._list[i][1]:
                self._list.insert(i, (item, priority))
                return

# If execution reaches here, the item doesn't have lesser priority than any of
# the elements in the queue.  Thus, append it to the end of the queue.
        self._list.append((item, priority))

    def get(self):
        """
        Return and remove the first item in the queue.
        """

        if self.isEmpty():
            raise IndexError("Get from empty queue.")
        return self._list.pop(0)[0]
