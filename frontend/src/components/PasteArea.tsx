import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { FileText } from "lucide-react";

interface Props {
  onAnalyze: (title: string, facts: string) => void;
}

const PasteArea = ({ onAnalyze }: Props) => {
  const [text, setText] = useState("");

  const handleAnalyze = () => {
    const lines = text.trim().split("\n");
    const title = lines[0] || "";
    const facts = lines.slice(1).join("\n");
    onAnalyze(title, facts);
  };

  return (
    <div className="rounded-lg border bg-card p-5 shadow-sm space-y-3">
      <h3 className="text-lg text-card-foreground flex items-center gap-2">
        <FileText className="h-5 w-5 text-accent" /> Or paste full case text
      </h3>
      <Textarea
        rows={4}
        placeholder="Paste the full case text here. The first line will be used as the case title."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <Button variant="outline" size="sm" disabled={!text.trim()} onClick={handleAnalyze}>
        Analyze text
      </Button>
    </div>
  );
};

export default PasteArea;
