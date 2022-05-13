from .scope_config_base import ScopeConfigureBase

class StripToolConfigure(ScopeConfigureBase):
    def __init__(self, params, **kwargs):
        super().__init__(params,
                         show_start=False,
                         **kwargs)

    def add_source_acquisition_props(self, children, section):
        children.append({"name": "Sample Mode", "type":"bool", "value": True})
        return children
    
    def parse(self):
        try:
            acquisition = self.assemble_acquisition(self.params["ACQUISITION"])
        except KeyError:
            acquisition = self.assemble_acquisition()

        try:
            display = self.assemble_display(self.params["DISPLAY"])
        except KeyError:
            display = self.assemble_display()
            
        statistics = self.assemble_statistics()
        # line up in order
        paramcfg = [acquisition, display, statistics]

        return paramcfg


