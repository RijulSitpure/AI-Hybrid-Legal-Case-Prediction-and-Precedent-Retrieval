import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Plus, RefreshCw, Cpu } from "lucide-react";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface Props {
  caseText?: string;
}

const SchedulerStatus = ({ caseText }: Props) => {
  const [status, setStatus] = useState<{ pending_cases: number; last_update: string; running: boolean } | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await api.schedulerStatus();
      setStatus(res.data);
    } catch {
      /* silent */
    }
  };

  useEffect(() => {
    fetchStatus();
    const id = setInterval(fetchStatus, 30000);
    return () => clearInterval(id);
  }, []);

  const addToQueue = async () => {
    if (!caseText) return;
    try {
      await api.addCase(caseText);
      toast.success("Case added to learning queue");
      fetchStatus();
    } catch {
      toast.error("Failed to add case to queue");
    }
  };

  const forceUpdate = async () => {
    try {
      await api.forceUpdate();
      toast.success("Model update triggered successfully");
      fetchStatus();
    } catch {
      toast.error("Failed to trigger model update");
    }
  };

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm flex flex-wrap items-center gap-4 text-sm font-body">
      <Cpu className="h-5 w-5 text-accent" />
      <span className="text-muted-foreground">
        Pending cases: <strong className="text-foreground">{status?.pending_cases ?? "–"}</strong>
      </span>
      <span className="text-muted-foreground">
        Last update: <strong className="text-foreground">{status?.last_update ?? "–"}</strong>
      </span>
      <span className="text-muted-foreground">
        Scheduler: <strong className={status?.running ? "text-success" : "text-muted-foreground"}>{status?.running ? "Active" : "–"}</strong>
      </span>

      <div className="ml-auto flex gap-2">
        <Button variant="outline" size="sm" disabled={!caseText} onClick={addToQueue} className="gap-1.5">
          <Plus className="h-3.5 w-3.5" /> Add to queue
        </Button>

        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="outline" size="sm" className="gap-1.5">
              <RefreshCw className="h-3.5 w-3.5" /> Force update
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Force model update?</AlertDialogTitle>
              <AlertDialogDescription>
                This will trigger an immediate incremental model update using all pending cases. This may take a few minutes.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={forceUpdate}>Confirm</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
};

export default SchedulerStatus;
