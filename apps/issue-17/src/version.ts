const K8S_VERSION_PATTERN = /^v?(?<major>\d+)\.(?<minor>\d+)$/;

export interface K8sVersion {
  major: number;
  minor: number;
  normalized: string;
}

export interface SupportedVersionRange {
  minMinor: number;
  maxMinor: number;
}

export function parseK8sVersion(input: string): K8sVersion {
  const trimmed = input.trim();
  const match = trimmed.match(K8S_VERSION_PATTERN);

  if (!match || !match.groups) {
    throw new Error(`Invalid Kubernetes version: "${input}". Use format like 1.28.`);
  }

  const major = Number.parseInt(match.groups.major, 10);
  const minor = Number.parseInt(match.groups.minor, 10);

  if (!Number.isFinite(major) || !Number.isFinite(minor)) {
    throw new Error(`Invalid Kubernetes version: "${input}". Use format like 1.28.`);
  }

  return {
    major,
    minor,
    normalized: `${major}.${minor}`
  };
}

export function compareK8sVersion(a: K8sVersion, b: K8sVersion): number {
  if (a.major !== b.major) {
    return a.major - b.major;
  }

  return a.minor - b.minor;
}

export function validateVersionPair(
  currentInput: string,
  targetInput: string,
  range: SupportedVersionRange
): { current: K8sVersion; target: K8sVersion } {
  const current = parseK8sVersion(currentInput);
  const target = parseK8sVersion(targetInput);

  if (current.major !== 1 || target.major !== 1) {
    throw new Error(
      `Unsupported Kubernetes major version. Supported Kubernetes versions: v1.${range.minMinor} ~ v1.${range.maxMinor}.`
    );
  }

  if (current.minor < range.minMinor || current.minor > range.maxMinor) {
    throw new Error(
      `Current version v${current.normalized} is outside supported range. Supported Kubernetes versions: v1.${range.minMinor} ~ v1.${range.maxMinor}.`
    );
  }

  if (target.minor < range.minMinor || target.minor > range.maxMinor) {
    throw new Error(
      `Target version v${target.normalized} is outside supported range. Supported Kubernetes versions: v1.${range.minMinor} ~ v1.${range.maxMinor}.`
    );
  }

  if (compareK8sVersion(target, current) < 0) {
    throw new Error(
      `Target version v${target.normalized} must be greater than or equal to current version v${current.normalized}.`
    );
  }

  return { current, target };
}

export function parseMilestone(version: string): K8sVersion {
  return parseK8sVersion(version);
}
