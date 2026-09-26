project = "Engineering traceability"
master_doc = "index"
extensions = ["sphinx_needs"]
needs_types = [
    {"directive": "req", "title": "Requirement", "prefix": "REQ_", "color": "#BFD8D2", "style": "node"},
    {"directive": "comp", "title": "Component", "prefix": "CMP_", "color": "#FEDCD2", "style": "node"},
    {"directive": "unit", "title": "Unit", "prefix": "UNT_", "color": "#DDEEFF", "style": "node"},
    {"directive": "test", "title": "Measure", "prefix": "TST_", "color": "#DDEEDD", "style": "node"},
    {"directive": "scenario", "title": "Scenario", "prefix": "SCN_", "color": "#EEE0FF", "style": "node"},
]
