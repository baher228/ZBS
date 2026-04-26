import { createFileRoute } from "@tanstack/react-router";
import { Bot, ExternalLink, Mic, MicOff, MousePointer2, Sparkles } from "lucide-react";
import type { FormEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  createLiveDemoSession,
  DemoEvent,
  DemoManifest,
  fetchLiveDemoManifest,
  LiveDemoSession,
  sendLiveDemoMessage,
} from "@/lib/agentApi";

export const Route = createFileRoute("/demo-room/live")({
  head: () => ({
    meta: [
      { title: "Live Demo Room - Demeo" },
      {
        name: "description",
        content: "Agent-led demo room over the extracted product app.",
      },
    ],
  }),
  component: LiveDemoRoom,
});

type Message = { role: "user" | "assistant"; content: string };
type CursorState = { x: number; y: number; clicking: boolean };
type HighlightRect = { x: number; y: number; width: number; height: number; label?: string };
type VoiceStatus = "disconnected" | "connecting" | "connected";
type VoiceFlowState = {
  flow_id?: string;
  step_id: string;
  step_index?: number;
  step_token: string;
  has_next: boolean;
};
type PendingVoiceStep = {
  token: number;
  flowId?: string;
  stepId: string;
  stepIndex?: number;
  stepToken: string;
  hasNext: boolean;
  visualsDone: boolean;
  audioStarted: boolean;
  speechDone: boolean;
};
type PendingVoicePlayback = {
  token: number;
  events: DemoEvent[];
  started: boolean;
};

declare global {
  interface Window {
    webkitAudioContext?: typeof AudioContext;
  }
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const suggestions = [
  "Walk me through the app setup.",
  "Show me what the agent demo room does.",
  "How does the agent know what it can click?",
  "What does the founder receive after the demo?",
];

function LiveDemoRoom() {
  const [manifest, setManifest] = useState<DemoManifest | null>(null);
  const [session, setSession] = useState<LiveDemoSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Loading the approved demo context...",
    },
  ]);
  const [input, setInput] = useState("");
  const [activePageId, setActivePageId] = useState("home");
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const [highlightRect, setHighlightRect] = useState<HighlightRect | null>(null);
  const [cursor, setCursor] = useState<CursorState>({ x: 180, y: 180, clicking: false });
  const [running, setRunning] = useState(false);
  const [actionLog, setActionLog] = useState<DemoEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [leadScore, setLeadScore] = useState(45);
  const [interestedFeatures, setInterestedFeatures] = useState<string[]>([]);
  const [liveNarration, setLiveNarration] = useState<string | null>(null);
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus>("disconnected");
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [inputTranscript, setInputTranscript] = useState("");
  const [outputTranscript, setOutputTranscript] = useState("");
  const [micLevel, setMicLevel] = useState(0);
  const [micPacketsSent, setMicPacketsSent] = useState(0);
  const [serverPacketsReceived, setServerPacketsReceived] = useState(0);
  const [speakerPacketsReceived, setSpeakerPacketsReceived] = useState(0);
  const [speakerSecondsQueued, setSpeakerSecondsQueued] = useState(0);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const playbackTokenRef = useRef(0);
  const playbackPageIdRef = useRef(activePageId);
  const voiceSocketRef = useRef<WebSocket | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const micAudioContextRef = useRef<AudioContext | null>(null);
  const micProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const outputAudioContextRef = useRef<AudioContext | null>(null);
  const outputSourcesRef = useRef<AudioBufferSourceNode[]>([]);
  const nextOutputTimeRef = useRef(0);
  const micMeterAtRef = useRef(0);
  const voiceConnectionTokenRef = useRef(0);
  const voiceStepTokenRef = useRef(0);
  const pendingVoiceStepRef = useRef<PendingVoiceStep | null>(null);
  const pendingVoicePlaybackRef = useRef<PendingVoicePlayback | null>(null);
  const audioIdleTimerRef = useRef<number | null>(null);

  const activePage = useMemo(
    () => manifest?.pages.find((page) => page.page_id === activePageId) ?? manifest?.pages[0],
    [activePageId, manifest],
  );
  const activeRoute =
    activePage?.route && activePage.route !== "/demo-room/live" ? activePage.route : "/";
  const visibleElementIds = useMemo(
    () => activePage?.elements.map((element) => element.id) ?? [],
    [activePage],
  );

  useEffect(() => {
    playbackPageIdRef.current = activePageId;
    sendVoicePageState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePageId]);

  useEffect(() => {
    document.body.classList.add("live-demo-mode");
    document.documentElement.classList.add("live-demo-native-cursor");

    async function boot() {
      try {
        const startupId =
          new URLSearchParams(window.location.search).get("startup_id") ?? undefined;
        const loadedManifest = await fetchLiveDemoManifest(apiBaseUrl, startupId);
        const firstPage = loadedManifest.pages[0];
        setManifest(loadedManifest);
        setMessages([
          {
            role: "assistant",
            content: buildOpeningMessage(loadedManifest),
          },
        ]);
        setActivePageId(firstPage.page_id);
        const created = await createLiveDemoSession(
          apiBaseUrl,
          loadedManifest.startup_id,
          firstPage.page_id,
        );
        setSession(created);
        setLeadScore(created.lead_profile.score);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to start live demo");
      }
    }

    void boot();
    return () => {
      document.body.classList.remove("live-demo-mode");
      document.documentElement.classList.remove("live-demo-native-cursor");
      stopVoice();
      abortPlayback();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, running]);

  const send = async (text: string) => {
    if (!text.trim() || running || !session) return;
    setError(null);
    abortPlayback();
    setRunning(true);
    setMessages((current) => [...current, { role: "user", content: text }]);
    setInput("");

    try {
      await sendWithSession(session, text);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Live demo request failed";
      if (message.includes("Live demo session not found") && manifest) {
        try {
          const recreated = await createLiveDemoSession(
            apiBaseUrl,
            manifest.startup_id,
            activePage?.page_id ?? manifest.pages[0].page_id,
          );
          setSession(recreated);
          await sendWithSession(recreated, text);
          setError(null);
        } catch (retryError) {
          setError(retryError instanceof Error ? retryError.message : "Live demo retry failed");
        }
      } else {
        setError(message);
      }
    } finally {
      setRunning(false);
    }
  };

  const sendWithSession = async (targetSession: LiveDemoSession, text: string) => {
    const response = await sendLiveDemoMessage(
      apiBaseUrl,
      targetSession.id,
      text,
      activePageId,
      visibleElementIds,
    );
    setSession(response.session);
    if (!response.events.some((event) => event.type === "say" && event.text)) {
      setMessages((current) => [...current, { role: "assistant", content: response.reply }]);
    }
    await runEvents(response.events);
  };

  const runEvents = async (events: DemoEvent[]) => {
    const playbackToken = ++playbackTokenRef.current;
    for (const event of events) {
      if (playbackToken !== playbackTokenRef.current) return;
      setActionLog((current) => [...current, event]);
      if (event.type === "say" && event.text) {
        setLiveNarration(event.text);
        setMessages((current) => {
          const last = current[current.length - 1];
          if (last?.role === "assistant" && last.content === event.text) return current;
          return [...current, { role: "assistant", content: event.text ?? "" }];
        });
        await waitForPlayback(playbackToken, event.duration_ms ?? 2200);
      }
      if (event.type === "navigate" && event.page_id) {
        playbackPageIdRef.current = event.page_id;
        setActivePageId(event.page_id);
        setHighlightedId(null);
        setHighlightRect(null);
        await waitForFrame(playbackToken, event.route);
      }
      if (event.type === "cursor.move" && event.element_id) {
        moveCursorTo(event.element_id);
        await waitForPlayback(playbackToken, event.duration_ms ?? 500);
      }
      if (event.type === "cursor.click") {
        setCursor((current) => ({ ...current, clicking: true }));
        await waitForPlayback(playbackToken, 180);
        setCursor((current) => ({ ...current, clicking: false }));
      }
      if (event.type === "highlight.show" && event.element_id) {
        setHighlightedId(event.element_id);
        measureHighlight(event.element_id, event.label ?? undefined);
      }
      if (event.type === "highlight.hide") {
        setHighlightedId(null);
        setHighlightRect(null);
      }
      if (event.type === "lead.profile.updated" && event.patch) {
        const score = event.patch.score;
        const features = event.patch.interested_features;
        if (typeof score === "number") setLeadScore(score);
        if (Array.isArray(features)) {
          setInterestedFeatures((current) => {
            const merged = [...current];
            features.forEach((feature) => {
              if (typeof feature === "string" && !merged.includes(feature)) merged.push(feature);
            });
            return merged;
          });
        }
      }
      if (event.type === "wait") {
        await waitForPlayback(playbackToken, event.duration_ms ?? 300);
      }
    }
    if (playbackToken === playbackTokenRef.current) {
      setLiveNarration(null);
    }
  };

  const findFrameElement = (elementId: string): Element | null => {
    const page = manifest?.pages.find((item) => item.page_id === playbackPageIdRef.current);
    const manifestElement = page?.elements.find((element) => element.id === elementId);
    const selector = manifestElement?.selector;
    const doc = iframeRef.current?.contentDocument;
    if (!doc) return null;
    return (
      findBySelector(doc, selector) ??
      findByText(doc, manifestElement?.label ?? "") ??
      findByText(doc, manifestElement?.description ?? "") ??
      findByText(doc, elementId) ??
      bestVisibleTarget(doc)
    );
  };

  const moveCursorTo = (elementId: string) => {
    requestAnimationFrame(() => {
      const iframe = iframeRef.current;
      const element = findFrameElement(elementId);
      if (!iframe || !element) return;
      settleElementInFrame(element);
      const iframeRect = iframe.getBoundingClientRect();
      const rect = visibleRect(element.getBoundingClientRect(), iframeRect);
      setCursor({
        x: iframeRect.left + rect.x + rect.width * 0.72,
        y: iframeRect.top + rect.y + Math.min(rect.height * 0.45, 80),
        clicking: false,
      });
    });
  };

  const measureHighlight = (elementId: string, label?: string) => {
    requestAnimationFrame(() => {
      const iframe = iframeRef.current;
      const element = findFrameElement(elementId);
      if (!iframe || !element) return;
      settleElementInFrame(element);
      const iframeRect = iframe.getBoundingClientRect();
      const rect = visibleRect(element.getBoundingClientRect(), iframeRect);
      setHighlightRect({
        x: iframeRect.left + rect.x,
        y: iframeRect.top + rect.y,
        width: rect.width,
        height: rect.height,
        label,
      });
    });
  };

  const waitForFrame = async (playbackToken: number, route?: string | null) => {
    const expectedPath = route?.split("?")[0];
    const startedAt = performance.now();
    while (performance.now() - startedAt < 1800) {
      if (playbackToken !== playbackTokenRef.current) return;
      const doc = iframeRef.current?.contentDocument;
      const framePath = iframeRef.current?.contentWindow?.location.pathname;
      const bodyReady = Boolean(doc?.body?.innerText?.trim());
      const routeReady = !expectedPath || framePath === expectedPath;
      if (bodyReady && routeReady) {
        await waitForPlayback(playbackToken, 160);
        return;
      }
      await wait(80);
    }
  };

  const abortPlayback = () => {
    playbackTokenRef.current += 1;
    cancelPendingVoiceStep();
    pendingVoicePlaybackRef.current = null;
    setHighlightedId(null);
    setHighlightRect(null);
    setLiveNarration(null);
    setCursor((current) => ({ ...current, clicking: false }));
  };

  const waitForPlayback = async (playbackToken: number, ms: number) => {
    const start = performance.now();
    while (performance.now() - start < ms) {
      await wait(Math.min(100, ms - (performance.now() - start)));
      if (playbackToken !== playbackTokenRef.current) return;
    }
  };

  const toggleVoice = () => {
    if (voiceStatus === "connected" || voiceStatus === "connecting") {
      stopVoice();
    } else {
      void startVoice();
    }
  };

  const startVoice = async () => {
    if (!session || !manifest || voiceStatus !== "disconnected") return;
    const connectionToken = ++voiceConnectionTokenRef.current;
    setVoiceError(null);
    setVoiceStatus("connecting");
    abortPlayback();
    try {
      await unlockOutputAudio();
      const voiceSession = await createLiveDemoSession(
        apiBaseUrl,
        manifest.startup_id,
        activePage?.page_id ?? manifest.pages[0].page_id,
      );
      if (connectionToken !== voiceConnectionTokenRef.current) return;
      setSession(voiceSession);
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
        },
      });
      if (connectionToken !== voiceConnectionTokenRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      micStreamRef.current = stream;
      setMicPacketsSent(0);
      setServerPacketsReceived(0);
      setSpeakerPacketsReceived(0);
      setSpeakerSecondsQueued(0);
      setMicLevel(0);

      const socket = new WebSocket(
        `${apiBaseUrl.replace(/^http/, "ws").replace(/\/$/, "")}/api/v1/live-demo/sessions/${voiceSession.id}/voice`,
      );
      voiceSocketRef.current = socket;

      socket.onopen = () => {
        if (
          connectionToken !== voiceConnectionTokenRef.current ||
          voiceSocketRef.current !== socket
        ) {
          socket.close();
          return;
        }
        setVoiceStatus("connected");
        sendVoicePageState(socket);
        socket.send(
          JSON.stringify({
            type: "text",
            message:
              "The prospect just joined this approved demo room. Greet them briefly using the current manifest. Explain the product's business purpose first, then offer to walk through the primary approved flow.",
          }),
        );
        startMicStreaming(stream, socket);
      };

      socket.onmessage = (event) => {
        if (
          connectionToken !== voiceConnectionTokenRef.current ||
          voiceSocketRef.current !== socket
        ) {
          return;
        }
        if (typeof event.data !== "string") return;
        const payload = JSON.parse(event.data);
        void handleVoiceServerEvent(payload);
      };

      socket.onerror = () => {
        if (
          connectionToken !== voiceConnectionTokenRef.current ||
          voiceSocketRef.current !== socket
        ) {
          return;
        }
        setVoiceError("Voice connection failed");
        stopVoice();
      };

      socket.onclose = () => {
        if (
          connectionToken !== voiceConnectionTokenRef.current ||
          voiceSocketRef.current !== socket
        ) {
          return;
        }
        stopMicStreaming();
        setVoiceStatus("disconnected");
      };
    } catch (err) {
      stopVoice();
      setVoiceError(err instanceof Error ? err.message : "Could not start voice");
    }
  };

  const stopVoice = () => {
    voiceConnectionTokenRef.current += 1;
    if (voiceSocketRef.current?.readyState === WebSocket.OPEN) {
      voiceSocketRef.current.send(JSON.stringify({ type: "audio_stream_end" }));
    }
    voiceSocketRef.current?.close();
    voiceSocketRef.current = null;
    cancelPendingVoiceStep();
    stopMicStreaming();
    stopOutputAudio();
    setVoiceStatus("disconnected");
  };

  const sendVoicePageState = (socket = voiceSocketRef.current) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(
      JSON.stringify({
        type: "page_state",
        current_page_id: activePageId,
        visible_element_ids: visibleElementIds,
      }),
    );
  };

  const handleVoiceServerEvent = async (payload: Record<string, unknown>) => {
    if (payload.type === "voice.ready") {
      setVoiceError(null);
      return;
    }
    if (payload.type === "error") {
      setVoiceError(String(payload.message ?? "Voice error"));
      return;
    }
    if (payload.type === "interrupted" || payload.type === "playback.pause") {
      abortPlayback();
      stopOutputAudio();
      return;
    }
    if (payload.type === "input_transcript" && typeof payload.text === "string") {
      setInputTranscript(payload.text);
      return;
    }
    if (payload.type === "audio.received") {
      const chunks = payload.chunks;
      if (typeof chunks === "number") setServerPacketsReceived(chunks);
      return;
    }
    if (payload.type === "output_transcript" && typeof payload.text === "string") {
      setOutputTranscript((current) => `${current}${payload.text}`);
      return;
    }
    if (payload.type === "audio" && typeof payload.data === "string") {
      await playPcm24(payload.data);
      void startPendingVoicePlayback();
      return;
    }
    if (payload.type === "voice.turn_complete") {
      const pendingStep = pendingVoiceStepRef.current;
      if (pendingStep?.audioStarted) {
        pendingStep.speechDone = true;
        maybeSendVoiceStepDone();
      }
      return;
    }
    if (payload.type === "voice.generation_complete") return;
    if (payload.type === "demo_response") {
      abortPlayback();
      stopOutputAudio();
      setOutputTranscript("");
      const flowState = parseVoiceFlowState(payload.flow_state);
      const voiceStepToken = ++voiceStepTokenRef.current;
      if (payload.voice_controlled && flowState?.has_next) {
        pendingVoiceStepRef.current = {
          token: voiceStepToken,
          flowId: flowState.flow_id,
          stepId: flowState.step_id,
          stepIndex: flowState.step_index,
          stepToken: flowState.step_token,
          hasNext: flowState.has_next,
          visualsDone: false,
          audioStarted: false,
          speechDone: false,
        };
      }
      if (payload.session) setSession(payload.session as LiveDemoSession);
      if (typeof payload.reply === "string" && !payload.voice_controlled) {
        setMessages((current) => [
          ...current,
          { role: "assistant", content: payload.reply as string },
        ]);
      }
      const events = (payload.events as DemoEvent[]) ?? [];
      if (payload.voice_controlled) {
        pendingVoicePlaybackRef.current = {
          token: voiceStepToken,
          events,
          started: false,
        };
      } else {
        await runEvents(events);
      }
      if (!payload.voice_controlled) {
        const pendingStep = pendingVoiceStepRef.current;
        if (pendingStep && pendingStep.token === voiceStepToken) {
          pendingStep.visualsDone = true;
          maybeSendVoiceStepDone();
        }
      }
    }
  };

  const parseVoiceFlowState = (value: unknown): VoiceFlowState | null => {
    if (!value || typeof value !== "object") return null;
    const item = value as Record<string, unknown>;
    if (
      typeof item.step_id !== "string" ||
      typeof item.step_token !== "string" ||
      typeof item.has_next !== "boolean"
    ) {
      return null;
    }
    return {
      flow_id: typeof item.flow_id === "string" ? item.flow_id : undefined,
      step_id: item.step_id,
      step_index: typeof item.step_index === "number" ? item.step_index : undefined,
      step_token: item.step_token,
      has_next: item.has_next,
    };
  };

  const clearAudioIdleTimer = () => {
    if (audioIdleTimerRef.current !== null) {
      window.clearTimeout(audioIdleTimerRef.current);
      audioIdleTimerRef.current = null;
    }
  };

  const cancelPendingVoiceStep = () => {
    clearAudioIdleTimer();
    pendingVoiceStepRef.current = null;
    voiceStepTokenRef.current += 1;
  };

  const startPendingVoicePlayback = async () => {
    const pendingPlayback = pendingVoicePlaybackRef.current;
    if (!pendingPlayback || pendingPlayback.started) return;
    pendingPlayback.started = true;
    await wait(650);
    if (pendingVoicePlaybackRef.current?.token !== pendingPlayback.token) return;
    if (pendingVoiceStepRef.current?.token !== pendingPlayback.token) return;
    await runEvents(pendingPlayback.events);
    if (pendingVoicePlaybackRef.current?.token === pendingPlayback.token) {
      pendingVoicePlaybackRef.current = null;
    }
    const pendingStep = pendingVoiceStepRef.current;
    if (pendingStep && pendingStep.token === pendingPlayback.token) {
      pendingStep.visualsDone = true;
      maybeSendVoiceStepDone();
    }
  };

  const isOutputAudioIdle = () => {
    const audioContext = outputAudioContextRef.current;
    if (!audioContext) return true;
    return (
      outputSourcesRef.current.length === 0 &&
      audioContext.currentTime >= nextOutputTimeRef.current - 0.05
    );
  };

  const maybeSendVoiceStepDone = () => {
    clearAudioIdleTimer();
    const scheduledStep = pendingVoiceStepRef.current;
    if (!scheduledStep) return;
    const scheduledToken = scheduledStep.token;
    audioIdleTimerRef.current = window.setTimeout(() => {
      const pendingStep = pendingVoiceStepRef.current;
      const socket = voiceSocketRef.current;
      if (
        pendingStep &&
        pendingStep.token === scheduledToken &&
        pendingStep.hasNext &&
        pendingStep.visualsDone &&
        pendingStep.audioStarted &&
        pendingStep.speechDone &&
        isOutputAudioIdle() &&
        socket?.readyState === WebSocket.OPEN
      ) {
        socket.send(
          JSON.stringify({
            type: "voice_step_done",
            flow_id: pendingStep.flowId,
            step_id: pendingStep.stepId,
            step_index: pendingStep.stepIndex,
            step_token: pendingStep.stepToken,
          }),
        );
        pendingVoiceStepRef.current = null;
      }
    }, 900);
  };

  const startMicStreaming = (stream: MediaStream, socket: WebSocket) => {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    const audioContext = new AudioContextClass();
    void audioContext.resume();
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    const silentOutput = audioContext.createGain();
    silentOutput.gain.value = 0;
    micAudioContextRef.current = audioContext;
    micProcessorRef.current = processor;

    processor.onaudioprocess = (event) => {
      if (socket.readyState !== WebSocket.OPEN) return;
      const input = event.inputBuffer.getChannelData(0);
      const now = performance.now();
      if (now - micMeterAtRef.current > 180) {
        micMeterAtRef.current = now;
        let sum = 0;
        for (let index = 0; index < input.length; index += 1) {
          sum += input[index] * input[index];
        }
        setMicLevel(Math.min(1, Math.sqrt(sum / input.length) * 8));
      }
      const pcm = floatTo16BitPcm(resampleTo16Khz(input, audioContext.sampleRate));
      if (pcm.byteLength > 0) {
        socket.send(pcm.buffer);
        setMicPacketsSent((current) => current + 1);
      }
    };
    source.connect(processor);
    processor.connect(silentOutput);
    silentOutput.connect(audioContext.destination);
  };

  const stopMicStreaming = () => {
    micProcessorRef.current?.disconnect();
    micProcessorRef.current = null;
    void micAudioContextRef.current?.close();
    micAudioContextRef.current = null;
    micStreamRef.current?.getTracks().forEach((track) => track.stop());
    micStreamRef.current = null;
    setMicLevel(0);
  };

  const playPcm24 = async (base64Audio: string) => {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    const audioContext =
      outputAudioContextRef.current ?? new AudioContextClass({ sampleRate: 24000 });
    outputAudioContextRef.current = audioContext;
    if (audioContext.state === "suspended") await audioContext.resume();

    const bytes = base64ToUint8Array(base64Audio);
    const samples = new Int16Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 2);
    const buffer = audioContext.createBuffer(1, samples.length, 24000);
    setSpeakerPacketsReceived((current) => current + 1);
    setSpeakerSecondsQueued((current) => current + buffer.duration);
    const channel = buffer.getChannelData(0);
    for (let index = 0; index < samples.length; index += 1) {
      channel[index] = Math.max(-1, Math.min(1, samples[index] / 32768));
    }

    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContext.destination);
    const pendingStep = pendingVoiceStepRef.current;
    if (pendingStep) pendingStep.audioStarted = true;
    const sourceStepToken = pendingStep?.token;
    const startAt = Math.max(audioContext.currentTime + 0.02, nextOutputTimeRef.current || 0);
    source.start(startAt);
    nextOutputTimeRef.current = startAt + buffer.duration;
    outputSourcesRef.current.push(source);
    source.onended = () => {
      outputSourcesRef.current = outputSourcesRef.current.filter((item) => item !== source);
      if (pendingVoiceStepRef.current?.token === sourceStepToken) {
        maybeSendVoiceStepDone();
      }
    };
  };

  const stopOutputAudio = () => {
    clearAudioIdleTimer();
    outputSourcesRef.current.forEach((source) => {
      try {
        source.stop();
      } catch {
        // Already stopped.
      }
    });
    outputSourcesRef.current = [];
    nextOutputTimeRef.current = 0;
  };

  const unlockOutputAudio = async () => {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    const audioContext =
      outputAudioContextRef.current ?? new AudioContextClass({ sampleRate: 24000 });
    outputAudioContextRef.current = audioContext;
    if (audioContext.state === "suspended") await audioContext.resume();

    const buffer = audioContext.createBuffer(1, 1, 24000);
    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContext.destination);
    source.start();
    nextOutputTimeRef.current = Math.max(nextOutputTimeRef.current, audioContext.currentTime);
  };

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void send(input);
  };

  return (
    <main className="min-h-screen bg-[#10120f] text-[#eff3e6]">
      <style>{`
        html.live-demo-native-cursor.custom-cursor,
        html.live-demo-native-cursor.custom-cursor *,
        html.live-demo-native-cursor,
        html.live-demo-native-cursor * { cursor: auto !important; }
        html.live-demo-native-cursor.custom-cursor a,
        html.live-demo-native-cursor.custom-cursor button,
        html.live-demo-native-cursor.custom-cursor [role="button"],
        html.live-demo-native-cursor a,
        html.live-demo-native-cursor button,
        html.live-demo-native-cursor [role="button"] { cursor: pointer !important; }
      `}</style>
      <div className="grid min-h-screen gap-2 p-2 lg:grid-cols-[minmax(0,1fr)_330px]">
        <section className="relative overflow-hidden border border-[#d8ff63]/20 bg-[#151913] shadow-[0_24px_80px_rgba(0,0,0,0.45)]">
          <Header
            productName={manifest?.product_name ?? "Extracted app"}
            activePageTitle={activePage?.title ?? activePageId}
            running={running}
          />
          <div className="grid min-h-[calc(100vh-78px)] grid-rows-[1fr_auto]">
            <div className="relative overflow-hidden p-2">
              <BrowserFrame
                iframeRef={iframeRef}
                activeRoute={activeRoute}
                activePageId={activePage?.page_id ?? activePageId}
                highlightedId={highlightedId}
                highlightRect={highlightRect}
                pages={manifest?.pages ?? []}
                liveNarration={liveNarration}
              />
              <DemoCursor cursor={cursor} />
            </div>
            <StatusStrip
              activePageId={activePage?.page_id ?? activePageId}
              highlightedId={highlightedId}
              leadScore={leadScore}
              features={interestedFeatures}
            />
          </div>
        </section>

        <aside className="grid min-h-screen gap-2 lg:grid-rows-[minmax(0,1fr)_190px]">
          <section className="flex min-h-0 flex-col border border-[#d8ff63]/20 bg-[#151913]">
            <div className="border-b border-[#d8ff63]/15 p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#8e9785]">
                    Demo Agent
                  </div>
                  <h1 className="mt-1 text-lg font-semibold tracking-normal text-[#f6ffe3]">
                    Demo Agent
                  </h1>
                </div>
                <div className="flex h-10 w-10 items-center justify-center border border-[#d8ff63]/35 bg-[#d8ff63]/10 text-[#d8ff63]">
                  <Bot className="h-5 w-5" />
                </div>
              </div>
            </div>

            <div ref={scrollRef} className="flex-1 space-y-2 overflow-y-auto p-3">
              {messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`border p-3 text-sm leading-6 ${
                    message.role === "user"
                      ? "ml-8 border-[#66d9ef]/25 bg-[#66d9ef]/10 text-[#dffaff]"
                      : "mr-8 border-[#d8ff63]/20 bg-[#0f130e] text-[#d8dece]"
                  }`}
                >
                  <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.18em] text-[#8e9785]">
                    {message.role === "user" ? "Prospect" : "Agent"}
                  </div>
                  {message.content}
                </div>
              ))}
              {running && (
                <div className="mr-8 border border-[#d8ff63]/20 bg-[#0f130e] p-3 font-mono text-xs text-[#d8ff63]">
                  planning visual events...
                </div>
              )}
            </div>

            <div className="border-t border-[#d8ff63]/15 p-3">
              {error && (
                <div className="mb-3 border border-[#ff5b58]/40 bg-[#ff5b58]/10 p-2 text-xs text-[#ffcbc7]">
                  {error}
                </div>
              )}
              <div className="mb-3 flex flex-wrap gap-2">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => void send(suggestion)}
                    disabled={running || !session}
                    className="border border-[#d8ff63]/20 px-2.5 py-1.5 text-left text-[11px] text-[#bfc8b6] transition-colors hover:border-[#d8ff63]/50 hover:text-[#f6ffe3] disabled:opacity-50"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
              <VoiceControl
                status={voiceStatus}
                inputTranscript={inputTranscript}
                outputTranscript={outputTranscript}
                micLevel={micLevel}
                micPacketsSent={micPacketsSent}
                serverPacketsReceived={serverPacketsReceived}
                speakerPacketsReceived={speakerPacketsReceived}
                speakerSecondsQueued={speakerSecondsQueued}
                error={voiceError}
                onToggle={toggleVoice}
                disabled={!session}
              />
              <form onSubmit={onSubmit} className="grid grid-cols-[1fr_auto] gap-2">
                <input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="Ask the agent to show setup, demo room, CRM..."
                  className="border border-[#d8ff63]/20 bg-[#0d100c] px-3 py-2 text-sm outline-none transition-colors placeholder:text-[#6f7769] focus:border-[#d8ff63]/60"
                />
                <button
                  type="submit"
                  disabled={running || !input.trim() || !session}
                  className="border border-[#d8ff63]/50 bg-[#d8ff63] px-4 py-2 text-sm font-semibold text-[#10120f] disabled:opacity-50"
                >
                  Send
                </button>
              </form>
            </div>
          </section>

          <ActionLog events={actionLog.slice(-9)} />
        </aside>
      </div>
    </main>
  );
}

function Header({
  productName,
  activePageTitle,
  running,
}: {
  productName: string;
  activePageTitle: string;
  running: boolean;
}) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[#d8ff63]/15 px-3 py-2">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center border border-[#d8ff63]/35 bg-[#d8ff63] text-[#10120f]">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#8e9785]">
            Live Demo Room
          </div>
          <div className="text-base font-semibold tracking-normal text-[#f6ffe3]">
            {productName}
          </div>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] text-[#bfc8b6]">
        <span className="border border-[#d8ff63]/20 px-2.5 py-1">page: {activePageTitle}</span>
        <span className="border border-[#66d9ef]/25 px-2.5 py-1 text-[#bdf5ff]">
          {running ? "agent planning" : "ready"}
        </span>
      </div>
    </header>
  );
}

function BrowserFrame({
  iframeRef,
  activeRoute,
  activePageId,
  highlightedId,
  highlightRect,
  pages,
  liveNarration,
}: {
  iframeRef: React.RefObject<HTMLIFrameElement | null>;
  activeRoute: string;
  activePageId: string;
  highlightedId: string | null;
  highlightRect: HighlightRect | null;
  pages: DemoManifest["pages"];
  liveNarration: string | null;
}) {
  const frameUrl = demoEmbedRoute(activeRoute);
  return (
    <div className="relative h-full min-h-[720px] overflow-hidden border border-[#d8ff63]/15 bg-[#0d100c]">
      <div className="flex items-center justify-between border-b border-[#d8ff63]/15 bg-[#11160f] px-3 py-2">
        <div className="flex min-w-0 items-center gap-2 font-mono text-[11px] text-[#aeb8a6]">
          <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#ffbd2e]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
          <span className="ml-3 truncate border border-[#d8ff63]/15 px-2 py-1">{activeRoute}</span>
        </div>
        <a
          href={activeRoute}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 font-mono text-[11px] text-[#d8ff63]"
        >
          open route <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>
      <div className="h-[calc(100%-41px)]">
        <div className="relative h-full min-w-0 bg-white">
          <div className="absolute left-3 top-3 z-[9996] flex max-w-[70%] gap-1 overflow-hidden">
            {pages.slice(0, 8).map((page, index) => (
              <div
                key={page.page_id}
                className={`border px-2 py-1 font-mono text-[10px] shadow-sm ${
                  page.page_id === activePageId
                    ? "border-[#d8ff63] bg-[#d8ff63] text-[#10120f]"
                    : "border-[#10120f]/10 bg-white/90 text-[#53604f]"
                }`}
              >
                {index + 1}. {page.page_id}
              </div>
            ))}
          </div>
          <iframe
            ref={iframeRef}
            key={activeRoute}
            src={frameUrl}
            title="Extracted product route"
            className="h-full w-full bg-white"
          />
          {highlightedId && highlightRect && (
            <div
              className="pointer-events-none fixed z-[9998] border-[3px] border-[#d8ff63] bg-[#d8ff63]/15 shadow-[0_0_0_9999px_rgba(16,18,15,0.28),0_0_42px_rgba(216,255,99,0.75)]"
              style={{
                left: highlightRect.x,
                top: highlightRect.y,
                width: highlightRect.width,
                height: highlightRect.height,
              }}
            >
              {highlightRect.label && (
                <div className="absolute -top-8 left-0 bg-[#d8ff63] px-2 py-1 font-mono text-[11px] font-semibold text-[#10120f] shadow-lg">
                  {highlightRect.label}
                </div>
              )}
            </div>
          )}
          {liveNarration && (
            <div className="pointer-events-none absolute bottom-4 left-4 right-4 z-[9997] border border-[#d8ff63]/30 bg-[#10120f]/95 p-3 text-[#eff3e6] shadow-[0_18px_50px_rgba(0,0,0,0.35)]">
              <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.2em] text-[#62745d]">
                Agent narration
              </div>
              <div className="text-sm leading-6">{liveNarration}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DemoCursor({ cursor }: { cursor: CursorState }) {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed left-0 top-0 z-[10000] transition-transform duration-500 ease-out"
      style={{ transform: `translate3d(${cursor.x}px, ${cursor.y}px, 0)` }}
    >
      <MousePointer2
        className={`h-8 w-8 -translate-x-1 -translate-y-1 rotate-[-10deg] text-[#d8ff63] drop-shadow-[0_0_14px_rgba(216,255,99,0.8)] ${
          cursor.clicking ? "scale-90" : "scale-100"
        }`}
      />
      <div
        className={`absolute left-2 top-2 h-8 w-8 border border-[#d8ff63]/60 transition-all ${
          cursor.clicking ? "scale-125 opacity-100" : "scale-75 opacity-0"
        }`}
      />
    </div>
  );
}

function StatusStrip({
  activePageId,
  highlightedId,
  leadScore,
  features,
}: {
  activePageId: string;
  highlightedId: string | null;
  leadScore: number;
  features: string[];
}) {
  return (
    <div className="grid gap-3 border-t border-[#d8ff63]/15 bg-[#11160f] p-3 font-mono text-[11px] text-[#aeb8a6] md:grid-cols-4">
      <span>current_page={activePageId}</span>
      <span>highlight={highlightedId ?? "none"}</span>
      <span>lead_score={leadScore}</span>
      <span>interest={features.slice(-1)[0] ?? "collecting"}</span>
    </div>
  );
}

function ActionLog({ events }: { events: DemoEvent[] }) {
  return (
    <section className="min-h-0 border border-[#d8ff63]/20 bg-[#151913]">
      <div className="border-b border-[#d8ff63]/15 p-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#8e9785]">
          Action Log
        </div>
      </div>
      <div className="max-h-[212px] space-y-2 overflow-y-auto p-3">
        {events.length === 0 && (
          <div className="text-sm text-[#899383]">Ask a question to watch events stream here.</div>
        )}
        {events.map((event) => (
          <div key={event.id} className="border border-[#d8ff63]/10 bg-[#0e120d] px-3 py-2">
            <div className="font-mono text-[11px] text-[#d8ff63]">{event.type}</div>
            <div className="mt-1 truncate text-xs text-[#aeb8a6]">
              {event.label ?? event.element_id ?? event.page_id ?? event.text ?? "state update"}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function VoiceControl({
  status,
  inputTranscript,
  outputTranscript,
  micLevel,
  micPacketsSent,
  serverPacketsReceived,
  speakerPacketsReceived,
  speakerSecondsQueued,
  error,
  onToggle,
  disabled,
}: {
  status: VoiceStatus;
  inputTranscript: string;
  outputTranscript: string;
  micLevel: number;
  micPacketsSent: number;
  serverPacketsReceived: number;
  speakerPacketsReceived: number;
  speakerSecondsQueued: number;
  error: string | null;
  onToggle: () => void;
  disabled: boolean;
}) {
  const connected = status === "connected";
  return (
    <div className="mb-3 border border-[#d8ff63]/15 bg-[#0e120d] p-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-[#8e9785]">
            Gemini Live voice
          </div>
          <div className="mt-1 text-xs text-[#aeb8a6]">
            {connected
              ? "Listening. Interrupt the walkthrough naturally."
              : status === "connecting"
                ? "Connecting realtime voice..."
                : "Start voice to let the agent greet and guide you."}
          </div>
        </div>
        <button
          type="button"
          onClick={onToggle}
          disabled={disabled}
          className={`inline-flex items-center gap-2 border px-3 py-2 text-xs font-semibold ${
            connected
              ? "border-[#ff5b58]/45 bg-[#ff5b58]/10 text-[#ffcbc7]"
              : "border-[#d8ff63]/45 bg-[#d8ff63] text-[#10120f]"
          } disabled:opacity-50`}
        >
          {connected ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          {connected ? "Stop" : status === "connecting" ? "Opening" : "Start voice"}
        </button>
      </div>
      {(inputTranscript || outputTranscript || error) && (
        <div className="mt-3 space-y-2 border-t border-[#d8ff63]/10 pt-3 font-mono text-[11px]">
          {inputTranscript && (
            <div className="text-[#bdf5ff]">you: {inputTranscript.slice(-180)}</div>
          )}
          {outputTranscript && (
            <div className="text-[#d8ff63]">agent: {outputTranscript.slice(-220)}</div>
          )}
          {error && <div className="text-[#ffcbc7]">voice_error: {error}</div>}
        </div>
      )}
      {status !== "disconnected" && (
        <div className="mt-3 border-t border-[#d8ff63]/10 pt-3">
          <div className="mb-2 flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.18em] text-[#8e9785]">
            <span>mic signal</span>
            <span>
              sent={micPacketsSent} server={serverPacketsReceived}
            </span>
          </div>
          <div className="h-2 border border-[#d8ff63]/20 bg-[#0a0d09]">
            <div
              className="h-full bg-[#d8ff63] transition-[width] duration-100"
              style={{ width: `${Math.round(micLevel * 100)}%` }}
            />
          </div>
          <div className="mt-2 font-mono text-[10px] uppercase tracking-[0.18em] text-[#8e9785]">
            speaker chunks={speakerPacketsReceived} queued={speakerSecondsQueued.toFixed(1)}s
          </div>
        </div>
      )}
    </div>
  );
}

function findBySelector(doc: Document, selector?: string): Element | null {
  if (!selector) return null;
  const textMatch = selector.match(/^([a-zA-Z0-9_-]+)?\s*:has-text\(["'](.+)["']\)$/);
  if (textMatch) {
    const tag = textMatch[1] || "*";
    const text = textMatch[2];
    return (
      Array.from(doc.querySelectorAll(tag)).find((item) => item.textContent?.includes(text)) ?? null
    );
  }
  if (selector.startsWith("text=")) {
    return findByText(doc, selector.slice(5));
  }
  try {
    return doc.querySelector(selector);
  } catch {
    return findByText(doc, selector.replace(/^text=/, ""));
  }
}

function findByText(doc: Document, text: string): Element | null {
  const trimmed = text.replace(/^["']|["']$/g, "").trim();
  if (!trimmed) return null;
  const normalizedNeedle = normalizeText(trimmed);
  const candidates = Array.from(
    doc.querySelectorAll(
      "button,a,input,textarea,[role='button'],[data-demo-id],label,h1,h2,h3,p,div",
    ),
  ).filter((item) => {
    if (!isUsableTarget(item)) return false;
    const candidateText = elementSearchText(item);
    return candidateText.includes(normalizedNeedle);
  });
  return smallestTarget(candidates);
}

function bestVisibleTarget(doc: Document): Element {
  const candidates = Array.from(
    doc.querySelectorAll("button,a,input,textarea,[data-demo-id],main,section,h1,h2"),
  );
  const visible = smallestTarget(candidates.filter(isUsableTarget));
  return visible ?? doc.body;
}

function elementSearchText(element: Element) {
  if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
    return normalizeText(
      `${element.placeholder} ${element.value} ${element.getAttribute("aria-label") ?? ""}`,
    );
  }
  return normalizeText(
    `${element.textContent ?? ""} ${element.getAttribute("aria-label") ?? ""} ${
      element.getAttribute("data-demo-id") ?? ""
    }`,
  );
}

function normalizeText(value: string) {
  return value.toLowerCase().replace(/\s+/g, " ").trim();
}

function isUsableTarget(element: Element) {
  const rect = element.getBoundingClientRect();
  const style = element.ownerDocument.defaultView?.getComputedStyle(element);
  return (
    rect.width >= 24 &&
    rect.height >= 18 &&
    rect.width <= 1200 &&
    rect.height <= 520 &&
    style?.visibility !== "hidden" &&
    style?.display !== "none"
  );
}

function smallestTarget(elements: Element[]) {
  return (
    elements
      .map((element) => ({ element, rect: element.getBoundingClientRect() }))
      .sort((a, b) => a.rect.width * a.rect.height - b.rect.width * b.rect.height)[0]?.element ??
    null
  );
}

function settleElementInFrame(element: Element) {
  const rect = element.getBoundingClientRect();
  const viewportHeight = element.ownerDocument.defaultView?.innerHeight ?? window.innerHeight;
  const viewportWidth = element.ownerDocument.defaultView?.innerWidth ?? window.innerWidth;
  const comfortablyVisible =
    rect.top >= 96 &&
    rect.left >= 24 &&
    rect.bottom <= viewportHeight - 96 &&
    rect.right <= viewportWidth - 24;
  if (!comfortablyVisible) {
    element.scrollIntoView({ block: "center", inline: "nearest", behavior: "auto" });
  }
}

function visibleRect(rect: DOMRect, iframeRect: DOMRect): HighlightRect {
  const padding = 8;
  const left = Math.max(padding, Math.min(rect.left, iframeRect.width - 96));
  const top = Math.max(padding, Math.min(rect.top, iframeRect.height - 72));
  const right = Math.min(iframeRect.width - padding, Math.max(left + 80, rect.right));
  const bottom = Math.min(iframeRect.height - padding, Math.max(top + 44, rect.bottom));
  return {
    x: left,
    y: top,
    width: Math.max(80, right - left),
    height: Math.max(44, bottom - top),
  };
}

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function buildOpeningMessage(manifest: DemoManifest) {
  const description = manifest.product_description?.trim().replace(/\.$/, "");
  const productIntro = description
    ? description
    : `${manifest.product_name} is built for ${manifest.target_persona}`;
  return `Hi, I’m the AI guide inside this ${manifest.product_name} demo room. ${productIntro}. Ask me to walk through the product, show a specific part, or explain what happens after the demo.`;
}

function demoEmbedRoute(route: string) {
  const separator = route.includes("?") ? "&" : "?";
  return `${route}${separator}demo_embed=1`;
}

function resampleTo16Khz(input: Float32Array, inputSampleRate: number) {
  if (inputSampleRate === 16000) return input;
  const outputLength = Math.max(1, Math.round((input.length * 16000) / inputSampleRate));
  const output = new Float32Array(outputLength);
  const ratio = inputSampleRate / 16000;
  for (let outputIndex = 0; outputIndex < outputLength; outputIndex += 1) {
    const sourceIndex = outputIndex * ratio;
    const lower = Math.floor(sourceIndex);
    const upper = Math.min(input.length - 1, lower + 1);
    const weight = sourceIndex - lower;
    output[outputIndex] = input[lower] * (1 - weight) + input[upper] * weight;
  }
  return output;
}

function floatTo16BitPcm(input: Float32Array) {
  const output = new Int16Array(input.length);
  for (let index = 0; index < input.length; index += 1) {
    const sample = Math.max(-1, Math.min(1, input[index]));
    output[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return output;
}

function base64ToUint8Array(value: string) {
  const binary = window.atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}
