"""
A unique ID class, and a factory for these IDs.
"""

class ObjectIDFactory(object):
    """
    A factory for IDs, guaranteed to be unique to them.
    """
    
    def __init__(self):
        object.__init__(self)
        self.nextLegalID = ObjectID(0)
    
    def get(self):
        ID = self.nextLegalID
        self.nextLegalID += 1
        return ID

class ObjectID(int):
    """
    A unique ID for an object.
    """
