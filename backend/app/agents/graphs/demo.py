from __future__ import annotations

from fastapi import HTTPException
from langgraph.graph import END, START, StateGraph

from app.agents.campaign_models import (
    ChatResponse,
    DemoChatGraphState,
    QualificationGraphState,
    QualificationReport,
)
from app.agents.capabilities import DemoAgent, SalesOpsAgent
from app.agents.llm import LLMProvider
from app.agents.store import InMemoryCampaignStore


class DemoChatGraphRunner:
    def __init__(self, llm_provider: LLMProvider, store: InMemoryCampaignStore) -> None:
        self.demo_agent = DemoAgent(llm_provider)
        self.store = store
        self.graph = self._compile_graph()

    def run(self, demo_room_id: str, message: str) -> ChatResponse:
        state = self.graph.invoke({"demo_room_id": demo_room_id, "message": message})
        return ChatResponse(
            demo_room_id=demo_room_id,
            reply=state["reply"],
            transcript=state["transcript"],
        )

    def _compile_graph(self):
        graph = StateGraph(DemoChatGraphState)
        graph.add_node("load_demo_room", self._load_demo_room)
        graph.add_node("demo_agent", self._demo_agent)
        graph.add_node("update_transcript", self._update_transcript)
        graph.add_edge(START, "load_demo_room")
        graph.add_edge("load_demo_room", "demo_agent")
        graph.add_edge("demo_agent", "update_transcript")
        graph.add_edge("update_transcript", END)
        return graph.compile()

    def _load_demo_room(self, state: DemoChatGraphState) -> DemoChatGraphState:
        demo_room = self.store.get_demo_room(state["demo_room_id"])
        if demo_room is None:
            raise HTTPException(status_code=404, detail="Demo room not found")
        return {"demo_room": demo_room}

    def _demo_agent(self, state: DemoChatGraphState) -> DemoChatGraphState:
        reply = self.demo_agent.reply(state["demo_room"], state["message"])
        return {"reply": reply}

    def _update_transcript(self, state: DemoChatGraphState) -> DemoChatGraphState:
        updated = self.store.append_demo_messages(
            state["demo_room_id"],
            state["message"],
            state["reply"],
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Demo room not found")
        return {"transcript": updated.transcript, "demo_room": updated}


class QualificationGraphRunner:
    def __init__(self, llm_provider: LLMProvider, store: InMemoryCampaignStore) -> None:
        self.sales_ops = SalesOpsAgent(llm_provider)
        self.store = store
        self.graph = self._compile_graph()

    def run(self, demo_room_id: str) -> QualificationReport:
        state = self.graph.invoke({"demo_room_id": demo_room_id})
        return state["qualification_report"]

    def _compile_graph(self):
        graph = StateGraph(QualificationGraphState)
        graph.add_node("load_transcript", self._load_transcript)
        graph.add_node("sales_ops", self._sales_ops)
        graph.add_node("persist_qualification", self._persist_qualification)
        graph.add_edge(START, "load_transcript")
        graph.add_edge("load_transcript", "sales_ops")
        graph.add_edge("sales_ops", "persist_qualification")
        graph.add_edge("persist_qualification", END)
        return graph.compile()

    def _load_transcript(self, state: QualificationGraphState) -> QualificationGraphState:
        demo_room = self.store.get_demo_room(state["demo_room_id"])
        if demo_room is None:
            raise HTTPException(status_code=404, detail="Demo room not found")
        if not demo_room.transcript:
            raise HTTPException(
                status_code=400,
                detail="Cannot qualify a demo room before the prospect has chatted.",
            )
        return {"demo_room": demo_room}

    def _sales_ops(self, state: QualificationGraphState) -> QualificationGraphState:
        return {"qualification_report": self.sales_ops.qualify(state["demo_room"])}

    def _persist_qualification(self, state: QualificationGraphState) -> QualificationGraphState:
        self.store.save_qualification(state["qualification_report"])
        return {}
