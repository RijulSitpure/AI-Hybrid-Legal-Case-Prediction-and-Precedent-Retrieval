import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { BarChart3, Brain, Target, Loader2, RotateCcw, Columns3, Scale } from "lucide-react";

export interface CaseFormData {
  title: string;
  facts: string | string[];
  violated_articles: string;
  judgment_date: string;
  retrieval_method: string;
}

interface Props {
  onPredict: (data: CaseFormData) => void;
  onCompare: (data: CaseFormData) => void;
  loading: boolean;
  formData: CaseFormData;
  setFormData: React.Dispatch<React.SetStateAction<CaseFormData>>;
}

const methods = [
  { value: "bm25", label: "BM25 (Keyword)", icon: BarChart3 },
  { value: "faiss", label: "FAISS (Semantic)", icon: Brain },
  { value: "hybrid", label: "Hybrid (Best of both)", icon: Target },
];

const CaseInput = ({ onPredict, onCompare, loading, formData, setFormData }: Props) => {
  const update = (key: keyof CaseFormData, val: string) =>
    setFormData((p) => ({ ...p, [key]: val }));

  const factsValue = typeof formData.facts === 'string' ? formData.facts : (Array.isArray(formData.facts) ? formData.facts.join('\n') : '');
  const canSubmit = formData.title.trim() && factsValue.trim() && !loading;

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm space-y-5">
      <h2 className="text-xl text-card-foreground">Case Details</h2>

      <div className="space-y-1.5">
        <Label className="font-body font-medium">Case Title</Label>
        <Input
          placeholder="e.g. CASE OF BECKER v. NORWAY"
          value={formData.title}
          onChange={(e) => update("title", e.target.value)}
        />
      </div>

      <div className="space-y-1.5">
        <Label className="font-body font-medium">Facts of the Case</Label>
        <Textarea
          placeholder="Enter the key facts, one per line or as a paragraph"
          rows={5}
          value={factsValue}
          onChange={(e) => update("facts", e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label className="font-body font-medium">Violated Articles (optional)</Label>
          <Input
            placeholder="e.g. Article 6, Article 8"
            value={formData.violated_articles}
            onChange={(e) => update("violated_articles", e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label className="font-body font-medium">Judgment Date (optional)</Label>
          <Input
            type="date"
            value={formData.judgment_date}
            onChange={(e) => update("judgment_date", e.target.value)}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label className="font-body font-medium">Retrieval Method</Label>
        <div className="flex flex-wrap gap-2">
          {methods.map((m) => {
            const Icon = m.icon;
            const active = formData.retrieval_method === m.value;
            return (
              <button
                key={m.value}
                onClick={() => update("retrieval_method", m.value)}
                className={`flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-body font-medium transition-colors ${
                  active
                    ? "border-accent bg-accent text-accent-foreground"
                    : "border-border bg-card text-muted-foreground hover:bg-muted"
                }`}
              >
                <Icon className="h-4 w-4" />
                {m.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 pt-2">
        <Button disabled={!canSubmit} onClick={() => onPredict(formData)} className="gap-2">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Scale className="h-4 w-4" />}
          Predict Outcome
        </Button>
        <Button
          variant="outline"
          onClick={() =>
            setFormData({ title: "", facts: "", violated_articles: "", judgment_date: new Date().toISOString().slice(0, 10), retrieval_method: "hybrid" })
          }
        >
          <RotateCcw className="mr-2 h-4 w-4" /> Clear
        </Button>
        <Button variant="outline" disabled={!canSubmit} onClick={() => onCompare(formData)} className="gap-2">
          <Columns3 className="h-4 w-4" /> Compare Methods
        </Button>
      </div>
    </div>
  );
};

export default CaseInput;
