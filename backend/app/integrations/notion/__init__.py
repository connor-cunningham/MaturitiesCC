"""
Notion Integration Layer (v2 hook)

To add Notion sync in a future phase:
1. Install: notion-client
2. Set NOTION_API_KEY and NOTION_BD_DATABASE_ID in .env
3. Implement NotionSyncAdapter below
4. Wire into CRM write operations in crm.py routes

Sync points:
- sync_owner(owner_id) → upsert Notion page in BD Owners database
- sync_note(note_id)   → push note as a block to linked Notion page
- sync_activity(activity_id) → log to Notion timeline
"""

from abc import ABC, abstractmethod


class NotionSyncAdapter(ABC):
    @abstractmethod
    async def sync_owner(self, owner_id: str) -> None: ...

    @abstractmethod
    async def sync_note(self, note_id: str) -> None: ...

    @abstractmethod
    async def sync_activity(self, activity_id: str) -> None: ...


class NoOpNotionAdapter(NotionSyncAdapter):
    async def sync_owner(self, owner_id: str) -> None:
        pass

    async def sync_note(self, note_id: str) -> None:
        pass

    async def sync_activity(self, activity_id: str) -> None:
        pass


notion_adapter = NoOpNotionAdapter()
