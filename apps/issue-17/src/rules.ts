import { ApiRule } from "./types";

export const SUPPORTED_VERSION_RANGE = {
  minMinor: 25,
  maxMinor: 34
};

export const API_RULES: ApiRule[] = [
  {
    id: "pdb-policy-v1beta1",
    kind: "PodDisruptionBudget",
    apiVersion: "policy/v1beta1",
    replacementApiVersion: "policy/v1",
    deprecatedIn: "1.21",
    removedIn: "1.25",
    reason: "policy/v1beta1 was removed for PodDisruptionBudget.",
    migration: "Update apiVersion to policy/v1 and ensure selector semantics are validated."
  },
  {
    id: "cronjob-batch-v1beta1",
    kind: "CronJob",
    apiVersion: "batch/v1beta1",
    replacementApiVersion: "batch/v1",
    deprecatedIn: "1.21",
    removedIn: "1.25",
    reason: "batch/v1beta1 CronJob was removed.",
    migration: "Update apiVersion to batch/v1 and verify schedule/concurrencyPolicy behavior."
  },
  {
    id: "ingress-extensions-v1beta1",
    kind: "Ingress",
    apiVersion: "extensions/v1beta1",
    replacementApiVersion: "networking.k8s.io/v1",
    deprecatedIn: "1.14",
    removedIn: "1.22",
    reason: "extensions/v1beta1 Ingress was removed.",
    migration: "Migrate to networking.k8s.io/v1 and set required pathType and backend.service fields."
  },
  {
    id: "ingress-networking-v1beta1",
    kind: "Ingress",
    apiVersion: "networking.k8s.io/v1beta1",
    replacementApiVersion: "networking.k8s.io/v1",
    deprecatedIn: "1.19",
    removedIn: "1.22",
    reason: "networking.k8s.io/v1beta1 Ingress was removed.",
    migration: "Migrate to networking.k8s.io/v1 and validate ingressClassName/pathType usage."
  },
  {
    id: "flowschema-v1beta2",
    kind: "FlowSchema",
    apiVersion: "flowcontrol.apiserver.k8s.io/v1beta2",
    replacementApiVersion: "flowcontrol.apiserver.k8s.io/v1",
    deprecatedIn: "1.26",
    removedIn: "1.29",
    reason: "FlowSchema v1beta2 was removed.",
    migration: "Migrate to flowcontrol.apiserver.k8s.io/v1."
  },
  {
    id: "priority-level-v1beta2",
    kind: "PriorityLevelConfiguration",
    apiVersion: "flowcontrol.apiserver.k8s.io/v1beta2",
    replacementApiVersion: "flowcontrol.apiserver.k8s.io/v1",
    deprecatedIn: "1.26",
    removedIn: "1.29",
    reason: "PriorityLevelConfiguration v1beta2 was removed.",
    migration: "Migrate to flowcontrol.apiserver.k8s.io/v1."
  },
  {
    id: "hpa-v2beta2",
    kind: "HorizontalPodAutoscaler",
    apiVersion: "autoscaling/v2beta2",
    replacementApiVersion: "autoscaling/v2",
    deprecatedIn: "1.23",
    removedIn: "1.26",
    reason: "autoscaling/v2beta2 HPA was removed.",
    migration: "Migrate to autoscaling/v2 and validate metrics schema."
  }
];
