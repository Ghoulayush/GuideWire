import pretext from "pretext";
import ProtectedDashboard from "@/components/ProtectedDashboard";

const story = `# GigShield Signal Deck

*Income protection* for delivery workers when cities break.

- _Onboard workers_ in seconds
- _Trigger disruptions_ as weather or social events happen
- _Auto-review payouts_ against fraud signals

Use the controls below to simulate your full insurance workflow.`;

export default function DashboardPage() {
  const storyHtml = pretext(story);

  return <ProtectedDashboard storyHtml={storyHtml} />;
}
