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
        self.last_item_priority = 0

    def __str__(self):
        strings = []
        for i in range(len(self._list)):
            strings.append("%d -- %d -- %s" % (i, self._list[i][1], str(self._list[i][0])))
        return "\n".join(strings)

    def __contains__(self, item):
        return item in [i[0] for i in self._list]

    def isEmpty(self):
        """
        Return True if the queue is empty, False otherwise.
        """
        return len(self._list) == 0

    def put(self, item, priority):
        """
        Put an item of priority 'priority' into the queue.
        """
        for i in range(len(self._list)):
            if priority < self._list[i][1]:
                self._list.insert(i, [item, priority])
                return

# If execution reaches here, the item doesn't have lesser priority than any of
# the elements in the queue.  Thus, append it to the end of the queue.
        self._list.append((item, priority))

    def priority_interval(self):
        """
        Return the difference in priority between the last item to be dequeued
        and the item at the front of the queue.
        """

        if self.isEmpty():
            raise IndexError("Interval request from empty queue.")
        return self._list[0][1] - self.last_item_priority

    def get(self):
        """
        Return and remove the first item in the queue.
        """
        if self.isEmpty():
            raise IndexError("Get from empty queue.")
        self.last_item_priority = self._list[0][1]
        return self._list.pop(0)[0]

    def erase(self, item):
        """
        Remove item completely from the queue, if it is in the queue.

        Raises a ValueError if the item is not in the queue.
        
        item - the item to be erased from the queue.
        
        """
        indices_to_erase = []
        for i in range(len(self._list)):
            if item == self._list[i][0]:
                indices_to_erase.insert(0, i)

        if indices_to_erase == []:
            raise ValueError("PriorityQueue.erase(): item not in queue")

        for index in indices_to_erase:
# Iterate BACKWARDS through the indices that should be erased.  This way,
# if indices 1 and 7 must be deleted, deleting 1 doesn't make 7 harder to reach
# (as it's now 6 instead).  indices_to_erase is already in decreasing order,
# so it's already backwards!
            del self._list[index]

        return
