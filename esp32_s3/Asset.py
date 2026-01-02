from Entity import Entity

class Asset(Entity):
    def __init__(self, id=0, version=0, code="", description="", isMsi=False):
        super().__init__(id, version, description)
        self.code = code
        self.isMsi = isMsi
