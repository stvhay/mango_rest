from pydantic import BaseModel
from typing import List, Optional

class PointLocator(BaseModel):
    dataType: str
    settable: bool
    relinquishable: bool|None
    configurationDescription: str
    monitorId: Optional[str]
    modelType: str

class LoggingProperties(BaseModel):
    loggingType: str
    tolerance: float
    discardExtremeValues: bool
    overrideIntervalLoggingSamples: bool
    cacheSize: int

class TextRenderer(BaseModel):
    useUnitAsSuffix: bool
    format: Optional[str]
    suffix: str
    type: str

class WatchListParameter(BaseModel):
    name: str
    type: str
    label: str
    options: dict

class WatchListSpec(BaseModel):
    readPermission: List[str]
    editPermission: List[str]
    type: str
    query:str|None
    params: List[WatchListParameter]
    data: dict
    id: int
    xid: str
    name: str

class Point(BaseModel):
    xid: str
    name: str
    deviceName: str
    readPermission: List[str]
    setPermission: List[str]

class FullPoint(Point):
      enabled: bool
      deviceName: str
      editPermission: List[str]
      purgeOverride: bool
      unit: str
      useIntegralUnit: bool
      useRenderedUnit: bool
      pointLocator: PointLocator
      chartColour: str
      plotType: str
      loggingProperties: LoggingProperties
      textRenderer: TextRenderer 
      rollup: str
      simplifyType: str
      simplifyTolerance: float
      simplifyTarget: int
      preventSetExtremeValues: bool
      data: dict|None
      dataSourceId: int
      dataSourceXid: str
      dataSourceName: str
      dataSourceTypeName: str
      tags: dict
      extendedName: str
      lifecycleState: str
      lifecycleStateTranslation: str
      id: int
      xid: str
      name: str

class WatchList(WatchListSpec):
    points: List[Point]

class PointList(BaseModel):
    items: List[FullPoint]

class WatchLists(BaseModel):
    items: List[WatchListSpec]
