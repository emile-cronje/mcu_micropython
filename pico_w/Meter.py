from Entity import Entity

class Meter(Entity):
    def __init__(self, id=0, version=0, code="", description="", isPaused=False, adr=0):
        super().__init__(id, version, description)
        self.code = code
        self.isPaused = isPaused
        self.adr = adr
