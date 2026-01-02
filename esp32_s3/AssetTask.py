from Entity import Entity

class AssetTask(Entity):
    def __init__(self, id=0, assetId=0, version=0, code="", description="", isRfs=False):
        super().__init__(id, version, description)
        self.code = code
        self.isRfs = isRfs
