import { Button } from "@/components/ui/button";
import { SampleCase } from "@/lib/api";
import { BookOpen } from "lucide-react";

interface Props {
  samples: SampleCase[];
  onSelect: (s: SampleCase) => void;
}

const labels = ["Privacy violation", "Length of proceedings", "Freedom of expression", "Unfair trial"];

const SampleCases = ({ samples, onSelect }: Props) => {
  if (!samples.length) return null;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-muted-foreground font-body flex items-center gap-1">
        <BookOpen className="h-4 w-4" /> Try a sample:
      </span>
      {samples.map((s, i) => (
        <Button
          key={i}
          variant="secondary"
          size="sm"
          className="font-body"
          onClick={() => onSelect(s)}
        >
          {labels[i] || s.title.slice(0, 30)}
        </Button>
      ))}
    </div>
  );
};

export default SampleCases;
