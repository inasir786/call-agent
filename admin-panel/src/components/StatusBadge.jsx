const LABELS = {
  pending: "Pending",
  calling: "Calling",
  no_answer: "No answer",
  reactivated: "Reactivated",
  nurture: "Nurture",
  closed_lost: "Closed-lost",
  invalid: "Invalid",
  failed: "Unreachable",
  needs_review: "Needs review",
}

export default function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{LABELS[status] || status}</span>
}
