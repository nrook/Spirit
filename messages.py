"""
Contains the MessageBuffer class.
"""

class MessageBuffer(object):
    """
    A container for the messages displayed to the player.

    Fields:
        dimensions - the dimensions of the array returned by getArray().
        message_list - a list of strings representing the messages sent.
            message_list[0] is the oldest message; message_list[-1] is the
            newest.
    """

    def __init__(self, dimensions, iterable_of_messages = None):
        """
        Create a MessageBuffer, of dimensions "dimensions", containing the
        messages in iterable_of_messages (or empty, if iterable_of_messages is
        None)

        dimensions - a tuple of two integers representing the horizontal and
            vertical length of the MessageBuffer, respectively.
        iterable_of_messages - something which, when iterated over, will
            produce (a finite number of) strings.  The last string in the
            iterable will be the "newest" message.
        """

        self.dimensions = dimensions
        if iterable_of_messages is None:
            self.message_list = []
        else:
            self.message_list = list(iterable_of_messages)

    def getArray(self):
        """
        Return an array representing the last few messages, where "the last few
        messages" are the last dimensions[1] messages.
        """

        ret_array = arrays.empty_str_array(self.dimensions)
        lines_to_use = self.message_list[-self.dimensions[1]:]
        lines_to_use.reverse()
        for i in range(len(lines_to_use)):
            print_str_to_end_of_line((0, i), lines_to_use[i], ret_array)

        return ret_array