"""Source-bridge package — Google Drive integration for 7 modules."""

from .bridge import (
    DEFAULT_SUBFOLDERS,
    DriveFile,
    GoogleDriveClient,
    IntakeCalculatorModule,
    LawLibraryModule,
    LayehaAppealWorkflowModule,
    MasterControlModule,
    MODULE_CLASSES,
    ModuleConfig,
    ModuleId,
    PagedQueueDashboardModule,
    RepositoryModule,
    SetupCaseIndexModule,
    SourceBridge,
    SourceBridgeError,
    SummarizerModule,
)
from .demo_client import (
    SAMPLE_FILES_META,
    DemoDriveClient,
    is_demo_mode,
    make_drive_client,
)

__all__ = [
    "DEFAULT_SUBFOLDERS",
    "DemoDriveClient",
    "DriveFile",
    "GoogleDriveClient",
    "IntakeCalculatorModule",
    "LawLibraryModule",
    "LayehaAppealWorkflowModule",
    "MasterControlModule",
    "MODULE_CLASSES",
    "ModuleConfig",
    "ModuleId",
    "PagedQueueDashboardModule",
    "RepositoryModule",
    "SAMPLE_FILES_META",
    "SetupCaseIndexModule",
    "SourceBridge",
    "SourceBridgeError",
    "SummarizerModule",
    "is_demo_mode",
    "make_drive_client",
]
