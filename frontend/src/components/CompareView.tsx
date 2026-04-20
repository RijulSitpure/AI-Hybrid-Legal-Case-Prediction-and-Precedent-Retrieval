import { motion } from "framer-motion";
import { X, BarChart3, Brain, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Precedent } from "@/lib/api";

interface Props {
  data: { bm25: Precedent[]; faiss: Precedent[]; hybrid: Precedent[] };
  onClose: () => void;
}

const columns = [
  { key: "bm25" as const, label: "BM25 (Keyword)", icon: BarChart3 },
  { key: "faiss" as const, label: "FAISS (Semantic)", icon: Brain },
  { key: "hybrid" as const, label: "Hybrid", icon: Target },
];

const CompareView = ({ data, onClose }: Props) => (
  <motion.div
    initial={{ opacity: 0, y: 16 }}
    animate={{ opacity: 1, y: 0 }}
    className="rounded-lg border bg-card p-6 shadow-sm space-y-4"
  >
    <div className="flex items-center justify-between">
      <h2 className="text-xl text-card-foreground">Method Comparison</h2>
      <Button variant="ghost" size="icon" onClick={onClose}>
        <X className="h-5 w-5" />
      </Button>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {columns.map((col) => {
        const Icon = col.icon;
        const items = data[col.key]?.slice(0, 3) || [];
        return (
          <div key={col.key} className="rounded-md border p-4 space-y-3">
            <div className="flex items-center gap-2 text-sm font-body font-semibold text-foreground">
              <Icon className="h-4 w-4 text-accent" /> {col.label}
            </div>
            {items.length === 0 ? (
              <p className="text-xs text-muted-foreground font-body">No results</p>
            ) : (
              items.map((p, i) => {
                const isV =
                  p.outcome?.toLowerCase().includes("violation") &&
                  !p.outcome?.toLowerCase().includes("no violation");
                return (
                  <div key={i} className="rounded bg-muted/40 p-2.5 space-y-1">
                    <p className="text-xs font-body font-semibold text-foreground line-clamp-1">
                      #{i + 1} {p.title}
                    </p>
                    <div className="flex items-center justify-between text-xs font-body">
                      <span className={isV ? "text-destructive" : "text-success"}>{p.outcome}</span>
                      <span className="text-muted-foreground">{typeof p.score === "number" ? p.score.toFixed(2) : p.score}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        );
      })}
    </div>
  </motion.div>
);

export default CompareView;
