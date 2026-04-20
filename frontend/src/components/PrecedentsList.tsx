import { motion } from "framer-motion";
import { BookOpen } from "lucide-react";
import type { Precedent } from "@/lib/api";

interface Props {
  precedents: Precedent[];
  method: string;
}

const methodLabels: Record<string, string> = {
  bm25: "BM25 (Keyword)",
  faiss: "FAISS (Semantic)",
  hybrid: "Hybrid",
};

const PrecedentsList = ({ precedents, method }: Props) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: 0.15 }}
    className="rounded-lg border bg-card p-6 shadow-sm space-y-4"
  >
    <h2 className="text-xl text-card-foreground flex items-center gap-2">
      <BookOpen className="h-5 w-5 text-accent" /> Similar Precedents
      <span className="text-sm font-body text-muted-foreground ml-auto">
        via {methodLabels[method] || method}
      </span>
    </h2>

    {precedents.length === 0 ? (
      <p className="text-sm text-muted-foreground font-body py-4 text-center">
        No similar cases found in the database.
      </p>
    ) : (
      <div className="space-y-3">
        {precedents.map((p, i) => {
          const isViolation =
            p.outcome?.toLowerCase().includes("violation") &&
            !p.outcome?.toLowerCase().includes("no violation");
          return (
            <div key={i} className="rounded-md border bg-muted/40 p-4 space-y-1">
              <div className="flex items-start justify-between gap-2">
                <p className="font-body font-semibold text-sm text-foreground">
                  <span className="text-accent mr-1.5">#{i + 1}</span>
                  {p.title}
                </p>
                <span
                  className={`shrink-0 rounded px-2 py-0.5 text-xs font-body font-medium ${
                    isViolation
                      ? "bg-destructive/15 text-destructive"
                      : "bg-success/15 text-success"
                  }`}
                >
                  {p.outcome}
                </span>
              </div>
              <div className="flex flex-wrap gap-3 text-xs text-muted-foreground font-body">
                <span>Relevance: {typeof p.relevance_score === "number" ? p.relevance_score.toFixed(2) : p.relevance_score}</span>
                {p.violated_articles && <span>Articles: {p.violated_articles}</span>}
              </div>
              {p.facts && p.facts.length > 0 && (
                <p className="text-xs text-muted-foreground font-body line-clamp-2 pt-1">
                  {Array.isArray(p.facts) ? p.facts.join(' ') : p.facts}
                </p>
              )}
            </div>
          );
        })}
      </div>
    )}
  </motion.div>
);

export default PrecedentsList;
