import { Scale } from "lucide-react";

const Header = () => (
  <header className="bg-primary px-6 py-5">
    <div className="container mx-auto flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Scale className="h-8 w-8 text-primary-foreground" />
        <div>
          <h1 className="text-2xl text-primary-foreground leading-tight">
            Legal AI Assistant – Case Predictor
          </h1>
          <p className="text-sm text-primary-foreground/70 font-body">
            Evidence‑based outcome prediction &amp; precedent retrieval
          </p>
        </div>
      </div>
      <div className="hidden sm:flex items-center gap-2 rounded-full bg-primary-foreground/10 px-3 py-1.5 text-xs text-primary-foreground font-body">
        <span className="h-2 w-2 rounded-full bg-success animate-pulse-glow" />
        Continuous learning active
      </div>
    </div>
  </header>
);

export default Header;
