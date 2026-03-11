function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '');
}

export function getPublicAppOrigin(): string {
  const configuredOrigin =
    process.env.NEXT_PUBLIC_APP_URL || process.env.NEXT_PUBLIC_URL;

  if (configuredOrigin && /^https?:\/\//i.test(configuredOrigin)) {
    return trimTrailingSlash(configuredOrigin);
  }

  if (typeof window !== 'undefined' && window.location?.origin) {
    return trimTrailingSlash(window.location.origin);
  }

  return 'http://localhost:3000';
}
