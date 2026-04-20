import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { api, type SampleCase, type Precedent } from "@/lib/api";
import Header from "@/components/Header";
import CaseInput, { type CaseFormData } from "@/components/CaseInput";
import SampleCases from "@/components/SampleCases";
import PasteArea from "@/components/PasteArea";
import PredictionResult from "@/components/PredictionResult";
import PrecedentsList from "@/components/PrecedentsList";
import CompareView from "@/components/CompareView";
import SchedulerStatus from "@/components/SchedulerStatus";

const defaultForm: CaseFormData = {
  title: "",
  facts: "",
  violated_articles: "",
  judgment_date: new Date().toISOString().slice(0, 10),
  retrieval_method: "hybrid",
};

const Index = () => {
  const [formData, setFormData] = useState<CaseFormData>(defaultForm);
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<{
    prediction: string;
    confidence: number;
    probability: { violation: number; no_violation: number };
  } | null>(null);
  const [precedents, setPrecedents] = useState<Precedent[]>([]);
  const [method, setMethod] = useState("hybrid");
  const [samples, setSamples] = useState<SampleCase[]>([]);
  const [compareData, setCompareData] = useState<{
    bm25: Precedent[];
    faiss: Precedent[];
    hybrid: Precedent[];
  } | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);

  useEffect(() => {
    api.sampleCases().then((r) => setSamples(r || [])).catch(() => {});
  }, []);

  const handlePredict = async (data: CaseFormData) => {
    setLoading(true);
    setPrediction(null);
    setPrecedents([]);
    setCompareData(null);
    try {
      const res = await api.predict({
        title: data.title,
        facts: data.facts,
        violated_articles: data.violated_articles || undefined,
        judgment_date: data.judgment_date || undefined,
        retrieval_method: data.retrieval_method,
      });
      if (res.success) {
        setPrediction(res.prediction);
        setPrecedents(res.precedents || []);
        setMethod(res.retrieval_method || data.retrieval_method);
      }
    } catch (e: any) {
      toast.error(e.message || "The server could not process your request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async (data: CaseFormData) => {
    setCompareLoading(true);
    setCompareData(null);
    try {
      const res = await api.compareMethods({
        title: data.title,
        facts: data.facts,
        violated_articles: data.violated_articles || undefined,
        judgment_date: data.judgment_date || undefined,
      });
      if (res.success) {
        setCompareData({
          bm25: res.bm25,
          faiss: res.faiss,
          hybrid: res.hybrid,
        });
      }
    } catch (e: any) {
      toast.error(e.message || "Failed to compare methods.");
    } finally {
      setCompareLoading(false);
    }
  };

  const handleSampleSelect = (s: SampleCase) => {
    const updated = {
      ...formData,
      title: s.title,
      facts: s.facts,
      violated_articles: s.violated_articles || "",
    };
    setFormData(updated);
    handlePredict(updated);
  };

  const handlePaste = (title: string, facts: string) => {
    setFormData((p) => ({ ...p, title, facts }));
  };

  const caseText = formData.title && formData.facts ? `${formData.title}\n${formData.facts}` : undefined;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 space-y-6 max-w-5xl">
        {/* Two-column on large screens */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: Input */}
          <div className="lg:col-span-3 space-y-4">
            <CaseInput
              formData={formData}
              setFormData={setFormData}
              onPredict={handlePredict}
              onCompare={handleCompare}
              loading={loading || compareLoading}
            />
            <SampleCases samples={samples} onSelect={handleSampleSelect} />
            <PasteArea onAnalyze={handlePaste} />
          </div>

          {/* Right: Result */}
          <div className="lg:col-span-2 space-y-4">
            {loading && (
              <div className="rounded-lg border bg-card p-10 flex flex-col items-center gap-3 shadow-sm">
                <Loader2 className="h-8 w-8 animate-spin text-accent" />
                <p className="text-sm font-body text-muted-foreground">Analyzing case…</p>
              </div>
            )}
            {prediction && !loading && (
              <PredictionResult
                prediction={prediction.prediction}
                confidence={prediction.confidence}
                probability={prediction.probability}
              />
            )}
          </div>
        </div>

        {/* Precedents */}
        {precedents.length > 0 && !loading && (
          <PrecedentsList precedents={precedents} method={method} />
        )}

        {/* Compare */}
        {compareLoading && (
          <div className="rounded-lg border bg-card p-10 flex flex-col items-center gap-3 shadow-sm">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
            <p className="text-sm font-body text-muted-foreground">Comparing retrieval methods…</p>
          </div>
        )}
        {compareData && !compareLoading && (
          <CompareView data={compareData} onClose={() => setCompareData(null)} />
        )}

        {/* Scheduler */}
        <SchedulerStatus caseText={caseText} />
      </main>
    </div>
  );
};

export default Index;
