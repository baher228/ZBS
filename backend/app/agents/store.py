from __future__ import annotations

from threading import RLock

from app.agents.campaign_models import CampaignResponse, ChatMessage, DemoRoom, QualificationReport


class InMemoryCampaignStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._campaigns: dict[str, CampaignResponse] = {}
        self._demo_rooms: dict[str, DemoRoom] = {}
        self._qualifications: dict[str, QualificationReport] = {}

    def save_campaign(self, campaign: CampaignResponse) -> None:
        with self._lock:
            self._campaigns[campaign.campaign_id] = campaign
            self._demo_rooms[campaign.demo_room.id] = campaign.demo_room

    def get_campaign(self, campaign_id: str) -> CampaignResponse | None:
        with self._lock:
            return self._campaigns.get(campaign_id)

    def get_demo_room(self, demo_room_id: str) -> DemoRoom | None:
        with self._lock:
            return self._demo_rooms.get(demo_room_id)

    def append_demo_messages(
        self, demo_room_id: str, user_message: str, assistant_message: str
    ) -> DemoRoom | None:
        with self._lock:
            demo_room = self._demo_rooms.get(demo_room_id)
            if demo_room is None:
                return None
            updated = demo_room.model_copy(
                update={
                    "transcript": [
                        *demo_room.transcript,
                        ChatMessage(role="user", content=user_message),
                        ChatMessage(role="assistant", content=assistant_message),
                    ]
                }
            )
            self._demo_rooms[demo_room_id] = updated
            campaign = self._campaigns.get(updated.campaign_id)
            if campaign is not None:
                self._campaigns[updated.campaign_id] = campaign.model_copy(
                    update={"demo_room": updated}
                )
            return updated

    def save_qualification(self, report: QualificationReport) -> None:
        with self._lock:
            self._qualifications[report.demo_room_id] = report

    def get_qualification(self, demo_room_id: str) -> QualificationReport | None:
        with self._lock:
            return self._qualifications.get(demo_room_id)

    def clear(self) -> None:
        with self._lock:
            self._campaigns.clear()
            self._demo_rooms.clear()
            self._qualifications.clear()


campaign_store = InMemoryCampaignStore()
