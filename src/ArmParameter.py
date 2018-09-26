class ArmParameter(object):
    default_value = None
    type_param = None
    meta_data = None

    def __init__(self, default_value, type_param, description):
        self.default_value = default_value
        self.type_param = type_param
        self.meta_data = MetaData(description)
    def to_dict(self):
        return {"defaultvalue": self.default_value, "type": self.type_param, "metadata": self.meta_data.to_dict()}

class MetaData(object):
    description = None
    def __init__(self, description):
        self.description = description
    def to_dict(self):
        return { "description": self.description} 