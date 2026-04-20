import { motion } from "framer-motion";
import { ShieldCheck, ShieldAlert } from "lucide-react";

interface Props {
  prediction: string;
  confidence: number;      // decimal between 0 and 1 (e.g., 0.87)
  probability: { violation: number; no_violation: number };
}

const PredictionResult = ({ prediction, confidence, probability }: Props) => {
  const isViolation = prediction.toLowerCase().includes("violation") && !prediction.toLowerCase().includes("no violation");
  const confidencePercent = confidence * 100;  // convert to percentage

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border bg-card p-6 shadow-sm space-y-4"
    >
      <h2 className="text-xl text-card-foreground">Prediction Result</h2>

      <div className="flex items-center gap-3">
        {isViolation ? (
          <ShieldAlert className="h-8 w-8 text-destructive" />
        ) : (
          <ShieldCheck className="h-8 w-8 text-success" />
        )}
        <span
          className={`rounded-md px-4 py-2 text-lg font-body font-semibold ${
            isViolation ? "bg-destructive text-destructive-foreground" : "bg-success text-success-foreground"
          }`}
        >
          {prediction.toUpperCase()}
        </span>
      </div>

      {/* Confidence bar */}
      <div className="space-y-1">
        <p className="text-sm font-body text-muted-foreground">Confidence</p>
        <div className="h-3 w-full rounded-full bg-muted overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${confidencePercent}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className={`h-full rounded-full ${isViolation ? "bg-destructive" : "bg-success"}`}
          />
        </div>
        <p className="text-right text-sm font-body font-semibold text-foreground">
          {confidencePercent.toFixed(1)}%
        </p>
      </div>

      {/* Probability breakdown */}
      <div className="grid grid-cols-2 gap-3 text-sm font-body">
        <div className="rounded-md bg-destructive/10 p-3 text-center">
          <p className="text-muted-foreground">Violation</p>
          <p className="text-lg font-semibold text-destructive">{(probability.violation * 100).toFixed(1)}%</p>
        </div>
        <div className="rounded-md bg-success/10 p-3 text-center">
          <p className="text-muted-foreground">No Violation</p>
          <p className="text-lg font-semibold text-success">{(probability.no_violation * 100).toFixed(1)}%</p>
        </div>
      </div>
    </motion.div>
  );
};

export default PredictionResult;