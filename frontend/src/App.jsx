import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  ChevronRight,
  LoaderCircle,
  RefreshCcw,
  Settings2,
  Sparkles,
} from "lucide-react";
import AppShell from "./components/AppShell";
import AiComposer from "./components/AiComposer";
import ActionItemsBoard from "./components/ActionItemsBoard";
import EmptyState from "./components/EmptyState";
import KpiCard from "./components/KpiCard";
import MeetingList from "./components/MeetingList";
import ResultsView from "./components/ResultsView";
import SectionCard from "./components/SectionCard";
import StatusPill from "./components/StatusPill";
import UploadDropzone from "./components/UploadDropzone";
import { ProcessingLayoutSkeleton } from "./components/Skeletons";
import { api } from "./lib/api";
import { formatDuration, safeJsonParse } from "./lib/formatters";

const initialJob = {
  id: "",
  filename: "",
  estimatedTime: "",
  status: "queued",
};

export default function App() {
  const [view, setView] = useState("dashboard");
  const [meetings, setMeetings] = useState([]);
  const [health, setHealth] = useState(null);
  const [selectedMeetingId, setSelectedMeetingId] = useState("");
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [loadingMeetings, setLoadingMeetings] = useState(true);
  const [loadingMeeting, setLoadingMeeting] = useState(false);
  const [meetingError, setMeetingError] = useState("");
  const [uploadFile, setUploadFile] = useState(null);
  const [summaryStyle, setSummaryStyle] = useState("executive");
  const [uploadError, setUploadError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeJob, setActiveJob] = useState(initialJob);
  const [composerPrompt, setComposerPrompt] = useState("");
  const [composerAnswer, setComposerAnswer] = useState("");
  const [composerError, setComposerError] = useState("");
  const [isAnsweringComposer, setIsAnsweringComposer] = useState(false);
  const pollingRef = useRef(null);

  async function loadHealth() {
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      setHealth({ status: "offline" });
    }
  }

  async function loadMeetings() {
    setLoadingMeetings(true);
    setMeetingError("");

    try {
      const data = await api.listMeetings();
      const list = data.meetings || [];
      setMeetings(list);

      if (!selectedMeetingId && list.length > 0) {
        setSelectedMeetingId(list[0].id);
      }
    } catch (error) {
      setMeetingError(error.message);
    } finally {
      setLoadingMeetings(false);
    }
  }

  async function loadMeeting(meetingId) {
    if (!meetingId) return;

    setLoadingMeeting(true);
    try {
      const data = await api.getMeeting(meetingId);
      setSelectedMeeting(data);
    } catch {
      setSelectedMeeting(null);
    } finally {
      setLoadingMeeting(false);
    }
  }

  useEffect(() => {
    loadHealth();
    loadMeetings();
  }, []);

  useEffect(() => {
    loadMeeting(selectedMeetingId);
  }, [selectedMeetingId]);

  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const totalDuration = useMemo(
    () => meetings.reduce((sum, item) => sum + Number(item.duration_secs || 0), 0),
    [meetings]
  );

  const totalActionItems = useMemo(
    () =>
      meetings.reduce(
        (count, meeting) => count + safeJsonParse(meeting.action_items, []).length,
        0
      ),
    [meetings]
  );

  const completedMeetings = meetings.filter((meeting) => meeting.status === "completed").length;
  const processingMeetings = meetings.filter((meeting) => meeting.status === "processing").length;
  const latestCompletedMeeting = meetings.find((meeting) => meeting.status === "completed") || null;

  async function handleUploadSubmit() {
    if (!uploadFile) {
      setUploadError("Choose a recording before starting the pipeline.");
      return;
    }

    setUploadError("");
    setIsSubmitting(true);

    try {
      const data = await api.uploadMeeting(uploadFile, summaryStyle);
      const nextJob = {
        id: data.meeting_id,
        filename: uploadFile.name,
        estimatedTime: data.estimated_time,
        status: data.status || "queued",
      };

      setActiveJob(nextJob);
      setView("processing");
      startPolling(nextJob.id);
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  function startPolling(meetingId) {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    pollingRef.current = setInterval(async () => {
      try {
        const statusData = await api.getStatus(meetingId);
        const status = statusData.status || "processing";

        setActiveJob((current) => ({ ...current, status }));

        if (status === "completed") {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          await loadMeetings();
          setSelectedMeetingId(meetingId);
          setView("results");
          setUploadFile(null);
        }

        if (String(status).startsWith("failed")) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          setUploadError(`Pipeline failed: ${status}`);
        }
      } catch {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }, 4000);
  }

  async function handleComposerAsk(question) {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) return;

    if (!latestCompletedMeeting) {
      setComposerError("There is no completed meeting yet. Upload and process a meeting first.");
      setComposerAnswer("");
      return;
    }

    setComposerError("");
    setComposerAnswer("");
    setIsAnsweringComposer(true);

    try {
      const responseText = await api.askMeeting(latestCompletedMeeting.id, trimmedQuestion);
      setComposerAnswer(responseText);
    } catch (error) {
      setComposerError(
        error.message || "I could not answer that question from the meeting right now."
      );
    } finally {
      setIsAnsweringComposer(false);
    }
  }

  async function handleSuggestionAsk(label) {
    setComposerPrompt(label);
    await handleComposerAsk(label);
  }

  const kpis = [
    {
      label: "Meetings captured",
      value: meetings.length,
      hint: "Across manual uploads and auto-detected recordings",
      tone: "warm",
    },
    {
      label: "Completed summaries",
      value: completedMeetings,
      hint: processingMeetings ? `${processingMeetings} still processing` : "All caught up",
      tone: "green",
    },
    {
      label: "Audio processed",
      value: formatDuration(totalDuration),
      hint: "Cumulative time analyzed by the pipeline",
      tone: "cool",
    },
    {
      label: "Open action items",
      value: totalActionItems,
      hint: "Grouped by meeting and ready for follow-through",
      tone: "default",
    },
  ];

  function renderDashboard() {
    if (!loadingMeetings && meetings.length === 0) {
      return (
        <div className="space-y-6">
          <AiComposer
            prompt={composerPrompt}
            onPromptChange={setComposerPrompt}
            onAsk={handleComposerAsk}
            onUpload={() => setView("upload")}
            onSuggestion={handleSuggestionAsk}
            answer={composerAnswer}
            answerContextLabel={latestCompletedMeeting?.filename}
            isAnswering={isAnsweringComposer}
            error={composerError}
            canAsk={Boolean(latestCompletedMeeting)}
          />
          <EmptyState
            title="No meetings yet"
            description="Start with a recording upload and the product will generate a structured summary, key points, and action dashboard. This redesign makes the first action explicit instead of hiding it behind tabs."
            ctaLabel="Upload first recording"
            onCta={() => setView("upload")}
          />
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <AiComposer
          prompt={composerPrompt}
          onPromptChange={setComposerPrompt}
          onAsk={handleComposerAsk}
          onUpload={() => setView("upload")}
          onSuggestion={handleSuggestionAsk}
          answer={composerAnswer}
          answerContextLabel={latestCompletedMeeting?.filename}
          isAnswering={isAnsweringComposer}
          error={composerError}
          canAsk={Boolean(latestCompletedMeeting)}
        />

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {kpis.map((item) => (
            <KpiCard key={item.label} {...item} />
          ))}
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <SectionCard
            eyebrow="Recent meetings"
            title="Keep the latest conversations in view"
            action={
              <button
                onClick={() => setView("results")}
                className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 transition hover:text-slate-950"
              >
                Open latest result
                <ChevronRight size={16} />
              </button>
            }
          >
            {loadingMeetings ? (
              <ProcessingLayoutSkeleton />
            ) : (
              <MeetingList
                meetings={meetings.slice(0, 4)}
                selectedMeetingId={selectedMeetingId}
                onSelect={(id) => {
                  setSelectedMeetingId(id);
                  setView("results");
                }}
              />
            )}
          </SectionCard>

          <SectionCard
            eyebrow="Follow-through"
            title="Action items by meeting"
            action={
              <div className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
                Collapsible groups
              </div>
            }
          >
            <ActionItemsBoard meetings={meetings.slice(0, 5)} />
          </SectionCard>
        </div>
      </div>
    );
  }

  function renderUpload() {
    return (
      <div className="space-y-6">
        <SectionCard
          eyebrow="Ingestion"
          title="Make the upload flow feel like the product"
          action={
            <div className="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-800">
              Clear next step
            </div>
          }
        >
          <p className="max-w-3xl text-sm leading-7 text-slate-600">
            The previous interface mixed stats, tabs, and upload controls in one dense view. This screen isolates the ingestion decision, gives the user one primary CTA, and keeps the summary-style choice visually obvious.
          </p>
        </SectionCard>

        <UploadDropzone
          file={uploadFile}
          onFileChange={setUploadFile}
          onClear={() => setUploadFile(null)}
          summaryStyle={summaryStyle}
          onSummaryStyleChange={setSummaryStyle}
          onSubmit={handleUploadSubmit}
          isSubmitting={isSubmitting}
          error={uploadError}
        />
      </div>
    );
  }

  function renderProcessing() {
    return (
      <div className="space-y-6">
        <SectionCard
          eyebrow="Processing"
          title="Hold the layout steady while the AI works"
          action={
            <StatusPill status={activeJob.status || "processing"} />
          }
        >
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="text-sm font-semibold text-slate-950">{activeJob.filename}</div>
              <div className="mt-2 text-sm text-slate-600">
                Estimated completion: {activeJob.estimatedTime || "Calculating"}
              </div>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-900">
              <LoaderCircle size={16} className="animate-spin" />
              Extracting audio, transcribing, and composing the brief
            </div>
          </div>
        </SectionCard>

        <ProcessingLayoutSkeleton />
      </div>
    );
  }

  function renderResults() {
    if (loadingMeetings) {
      return <ProcessingLayoutSkeleton />;
    }

    if (!selectedMeeting && meetings.length === 0) {
      return (
        <EmptyState
          title="No results yet"
          description="Once a meeting has finished processing, the summary and action items will appear here."
          ctaLabel="Go to upload"
          onCta={() => setView("upload")}
        />
      );
    }

    return (
      <div className="space-y-6">
        <div className="grid gap-6 xl:grid-cols-[340px_1fr]">
          <SectionCard eyebrow="Library" title="All meetings">
            <MeetingList
              meetings={meetings}
              selectedMeetingId={selectedMeetingId}
              onSelect={setSelectedMeetingId}
            />
          </SectionCard>
          {loadingMeeting ? <ProcessingLayoutSkeleton /> : <ResultsView meeting={selectedMeeting} />}
        </div>
      </div>
    );
  }

  function renderActionItems() {
    return (
      <div className="space-y-6">
        <SectionCard
          eyebrow="Team execution"
          title="Action items dashboard"
          action={
            <div className="flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-soft">
              <Sparkles size={14} />
              Grouped by meeting
            </div>
          }
        >
          <p className="max-w-3xl text-sm leading-7 text-slate-600">
            This view borrows the collapsible hierarchy from the reference but improves scanning with stronger grouping, richer task metadata, and cleaner status treatments. It is designed for follow-through, not just display.
          </p>
        </SectionCard>

        <ActionItemsBoard meetings={meetings} />
      </div>
    );
  }

  function renderAgenda() {
    return (
      <SectionCard
        eyebrow="Agenda"
        title="Agenda workspace"
        action={
          <div className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-slate-700">
            Coming next
          </div>
        }
      >
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-[24px] bg-stone-950 p-6 text-white">
            <div className="text-sm font-semibold text-stone-200">Suggested agenda prompt</div>
            <div className="mt-4 text-2xl font-bold tracking-[-0.03em]">
              {composerPrompt || "Ask AI to draft a focused agenda from your last meeting."}
            </div>
            <p className="mt-3 text-sm leading-7 text-stone-300">
              Keeping agenda planning inside the same workspace closes the loop between decisions and the next conversation.
            </p>
          </div>
          <div className="rounded-[24px] border hairline bg-white p-6">
            <div className="text-sm font-semibold text-slate-950">Recommended sections</div>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-slate-600">
              <li>1. Review open action items and blockers.</li>
              <li>2. Confirm decisions made since the last meeting.</li>
              <li>3. Resolve risks that are approaching deadlines.</li>
              <li>4. Assign owners for any unclaimed next steps.</li>
            </ul>
          </div>
        </div>
      </SectionCard>
    );
  }

  function renderSettings() {
    return (
      <div className="space-y-6">
        <SectionCard
          eyebrow="Settings"
          title="Environment and product controls"
          action={
            <button
              onClick={() => {
                loadHealth();
                loadMeetings();
              }}
              className="inline-flex items-center gap-2 rounded-2xl border hairline bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5 hover:shadow-soft"
            >
              <RefreshCcw size={16} />
              Refresh
            </button>
          }
        >
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-[24px] border hairline bg-stone-50 p-5">
              <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                <Settings2 size={14} />
                API status
              </div>
              <div className="mt-4">
                <StatusPill status={health?.status === "ok" ? "completed" : "failed"} />
              </div>
            </div>
            <div className="rounded-[24px] border hairline bg-stone-50 p-5">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                LLM provider
              </div>
              <div className="mt-4 text-lg font-bold text-slate-950">
                {health?.llm_provider || "Unavailable"}
              </div>
            </div>
            <div className="rounded-[24px] border hairline bg-stone-50 p-5">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Meeting count
              </div>
              <div className="mt-4 text-lg font-bold text-slate-950">{meetings.length}</div>
            </div>
          </div>
        </SectionCard>
      </div>
    );
  }

  return (
    <AppShell currentView={view} onNavigate={setView} health={health}>
      {meetingError ? (
        <div className="mb-6 rounded-[24px] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-800">
          {meetingError}
        </div>
      ) : null}

      {view === "dashboard" && renderDashboard()}
      {view === "upload" && renderUpload()}
      {view === "processing" && renderProcessing()}
      {view === "results" && renderResults()}
      {view === "action-items" && renderActionItems()}
      {view === "agenda" && renderAgenda()}
      {view === "settings" && renderSettings()}

      {view !== "upload" ? (
        <button
          onClick={() => setView("upload")}
          className="fixed bottom-6 right-6 inline-flex items-center gap-2 rounded-full bg-stone-950 px-5 py-4 text-sm font-semibold text-white shadow-panel transition hover:-translate-y-0.5 hover:bg-stone-800"
        >
          Upload new recording
          <ArrowRight size={16} />
        </button>
      ) : null}
    </AppShell>
  );
}
