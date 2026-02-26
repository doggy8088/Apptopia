import { AnalysisResult, ExecutionPlan } from "./types";

export function buildExecutionPlan(analysis: AnalysisResult): ExecutionPlan {
  const steps = [
    {
      id: "step-1",
      name: "Ingest project documents",
      owner: "project-analysis-agent",
      required_skills: ["requirement-analysis-skill"],
      input_dependencies: analysis.sourceFiles,
      expected_output: "Normalized project summary and extracted requirements.",
      retry_behavior: "Retry once after clarifying missing inputs.",
      review_points: ["Confirm key goals and constraints are captured."]
    },
    {
      id: "step-2",
      name: "Map capabilities",
      owner: "capability-mapping-agent",
      required_skills: ["capability-mapping-skill"],
      input_dependencies: ["step-1"],
      expected_output: "Required capability list with categories.",
      retry_behavior: "Escalate if taxonomy mapping is ambiguous.",
      review_points: ["Validate coverage against provided taxonomy."]
    },
    {
      id: "step-3",
      name: "Compare registry coverage",
      owner: "registry-governance-agent",
      required_skills: ["registry-compare-skill"],
      input_dependencies: ["step-2"],
      expected_output: "Coverage report with covered/partial/missing status.",
      retry_behavior: "Retry after registry validation fixes.",
      review_points: ["Resolve duplicate or overlapping registry entries."]
    },
    {
      id: "step-4",
      name: "Generate missing definitions",
      owner: "definition-factory-agent",
      required_skills: ["skill-definition-generation", "agent-definition-generation"],
      input_dependencies: ["step-3"],
      expected_output: "Draft skill and agent definitions for missing capabilities.",
      retry_behavior: "Generate alternative drafts if conflicts persist.",
      review_points: ["Review rationale for skill vs agent classification."]
    },
    {
      id: "step-5",
      name: "Finalize execution plan",
      owner: "project-lead-agent",
      required_skills: ["execution-planning-skill"],
      input_dependencies: ["step-4"],
      expected_output: "Approved execution plan with owners and dependencies.",
      retry_behavior: "Revise plan after stakeholder feedback.",
      review_points: ["Confirm owners, dependencies, and deliverables."]
    }
  ];

  const dependencies = [
    { from: "step-1", to: "step-2" },
    { from: "step-2", to: "step-3" },
    { from: "step-3", to: "step-4" },
    { from: "step-4", to: "step-5" }
  ];

  const owners = Array.from(new Set(steps.map((step) => step.owner)));

  return { steps, dependencies, owners };
}
