from Entity import Entity

class MeterReading(Entity):
    def __init__(self, id=0, version=0, meterId=None, reading=None, readingOn=None):
        super().__init__(id, version, description=None)
        self.meterId = meterId
        self.reading = reading
        self.readingOn = readingOn        
