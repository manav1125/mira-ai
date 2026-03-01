interface HtmlPreviewUrlOptions {
  sandboxId?: string;
  accessToken?: string;
  preferBackendProxy?: boolean;
  inline?: boolean;
}

export function normalizeSandboxBaseUrl(sandboxUrl: string | undefined): string | undefined {
  if (!sandboxUrl) return undefined;

  try {
    const parsed = new URL(sandboxUrl);
    const hostname = parsed.hostname.toLowerCase();
    const isDaytonaHost = hostname.includes('daytona');
    const isProxyHost = hostname.includes('proxy');
    if (parsed.protocol === 'http:' && (isDaytonaHost || isProxyHost)) {
      parsed.protocol = 'https:';
      return parsed.toString().replace(/\/+$/, '');
    }
    return sandboxUrl.replace(/\/+$/, '');
  } catch {
    return sandboxUrl.replace(/\/+$/, '');
  }
}

export function extractSandboxIdFromSandboxUrl(sandboxUrl: string | undefined): string | undefined {
  if (!sandboxUrl) return undefined;

  try {
    const parsed = new URL(sandboxUrl);
    const hostname = parsed.hostname.toLowerCase();
    const isDaytonaHost = hostname.includes('daytona');
    const firstLabel = parsed.hostname.split('.')[0];
    if (!firstLabel) return undefined;

    // Daytona preview host commonly uses "<port>-<sandbox-id>.<domain>"
    const portPrefixedMatch = firstLabel.match(/^\d+-(.+)$/);
    if (portPrefixedMatch?.[1] && isDaytonaHost) {
      return portPrefixedMatch[1];
    }

    // Fallback for sandbox-id-like host labels on Daytona domains.
    if (isDaytonaHost) {
      const plainIdMatch = firstLabel.match(/^[a-zA-Z0-9-]{8,}$/);
      if (plainIdMatch) {
        return firstLabel;
      }
    }

    // Fallback for UUID-looking host labels on non-Daytona custom domains.
    const uuidMatch = firstLabel.match(/[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i);
    if (uuidMatch?.[0]) return uuidMatch[0];
  } catch {
    return undefined;
  }

  return undefined;
}

function safeDecodeURIComponent(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

function extractWorkspacePathFromFilePath(filePath: string): string | undefined {
  let processedPath = filePath;

  // If filePath is a full URL (API endpoint), extract the path parameter
  if (filePath.includes('://') || filePath.includes('/sandboxes/') || filePath.includes('/files/content')) {
    try {
      // Try to parse as URL if it's a full URL
      if (filePath.includes('://')) {
        const url = new URL(filePath);
        const pathParam = url.searchParams.get('path');
        if (pathParam) {
          processedPath = safeDecodeURIComponent(pathParam);
        } else {
          // Handle direct preview URLs like:
          // https://8080-<sandbox>.daytonaproxy01.net/presentations/foo/slide_01.html
          const pathname = safeDecodeURIComponent(url.pathname || '');

          if (pathname.startsWith('/workspace/')) {
            processedPath = pathname;
          } else if (pathname.startsWith('/presentations/')) {
            processedPath = pathname;
          } else {
            const workspaceIndex = pathname.indexOf('/workspace/');
            const presentationsIndex = pathname.indexOf('/presentations/');

            if (workspaceIndex >= 0) {
              processedPath = pathname.slice(workspaceIndex);
            } else if (presentationsIndex >= 0) {
              processedPath = pathname.slice(presentationsIndex);
            } else {
              // If no path param, try to extract from pathname
              // Handle patterns like /v1/sandboxes/.../files/content?path=...
              const pathMatch = filePath.match(/[?&]path=([^&]+)/);
              if (pathMatch) {
                processedPath = safeDecodeURIComponent(pathMatch[1]);
              } else {
                // If it's a relative URL with /sandboxes/ pattern, extract the path
                const sandboxMatch = filePath.match(/\/sandboxes\/[^\/]+\/files\/content[?&]path=([^&]+)/);
                if (sandboxMatch) {
                  processedPath = safeDecodeURIComponent(sandboxMatch[1]);
                } else {
                  // If this looks like a direct HTML/JSON file URL, use pathname as-is.
                  if (pathname.endsWith('.html') || pathname.endsWith('.htm') || pathname.endsWith('.json')) {
                    processedPath = pathname;
                  } else {
                    // Can't extract path
                    return undefined;
                  }
                }
              }
            }
          }
        }
      } else {
        // Relative URL pattern: /sandboxes/.../files/content?path=...
        const pathMatch = filePath.match(/[?&]path=([^&]+)/);
        if (pathMatch) {
          processedPath = safeDecodeURIComponent(pathMatch[1]);
        } else {
          // Can't extract path
          return undefined;
        }
      }
    } catch (e) {
      // If URL parsing fails, treat as regular path
      console.warn('Failed to parse filePath as URL, treating as regular path:', filePath);
    }
  }

  // Normalize to /workspace/... because backend file API expects workspace-absolute paths.
  if (processedPath === 'workspace' || processedPath.startsWith('workspace/')) {
    processedPath = `/${processedPath}`;
  } else if (!processedPath.startsWith('/workspace')) {
    processedPath = `/workspace/${processedPath.replace(/^\/+/, '')}`;
  }

  return processedPath;
}

/**
 * Constructs a preview URL for HTML files in the sandbox environment.
 * Properly handles URL encoding of file paths by encoding each path segment individually.
 *
 * @param sandboxUrl - The base URL of the sandbox
 * @param filePath - The path to the HTML file (can include /workspace/ prefix, or be a full API URL)
 * @param options - Optional URL construction behavior
 * @returns The properly encoded preview URL, or undefined if inputs are invalid
 */
export function constructHtmlPreviewUrl(
  sandboxUrl: string | undefined,
  filePath: string | undefined,
  options?: HtmlPreviewUrlOptions,
): string | undefined {
  const normalizedSandboxUrl = normalizeSandboxBaseUrl(sandboxUrl);
  if (!normalizedSandboxUrl || !filePath) {
    return undefined;
  }

  const workspacePath = extractWorkspacePathFromFilePath(filePath);
  if (!workspacePath) {
    return undefined;
  }

  const effectiveSandboxId = options?.sandboxId || extractSandboxIdFromSandboxUrl(normalizedSandboxUrl);

  if (options?.preferBackendProxy && effectiveSandboxId) {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || '';
    if (backendUrl) {
      try {
        const normalizedBackendUrl = backendUrl.startsWith('http')
          ? backendUrl
          : `${typeof window !== 'undefined' ? window.location.origin : ''}${backendUrl.startsWith('/') ? '' : '/'}${backendUrl}`;
        const apiUrl = new URL(`${normalizedBackendUrl.replace(/\/+$/, '')}/sandboxes/${effectiveSandboxId}/files/content`);
        apiUrl.searchParams.append('path', workspacePath);
        if (options.accessToken) {
          apiUrl.searchParams.append('token', options.accessToken);
        }
        if (options.inline !== false) {
          apiUrl.searchParams.append('inline', 'true');
        }
        return apiUrl.toString();
      } catch (e) {
        console.warn('Failed to build backend HTML preview URL, falling back to sandbox URL:', e);
      }
    }
  }

  let processedPath = workspacePath;

  // Remove /workspace/ prefix if present
  processedPath = processedPath.replace(/^\/workspace\//, '');

  // Split the path into segments and encode each segment individually
  const pathSegments = processedPath
    .split('/')
    .filter(Boolean) // Remove empty segments
    .map((segment) => encodeURIComponent(segment));

  // Join the segments back together with forward slashes
  const encodedPath = pathSegments.join('/');

  return `${normalizedSandboxUrl}/${encodedPath}`;
}

/**
 * Safely append or replace a query param on a URL string.
 */
export function withQueryParam(
  url: string | undefined,
  key: string,
  value: string | number | boolean,
): string | undefined {
  if (!url) return undefined;

  try {
    const parsed = new URL(url);
    parsed.searchParams.set(key, String(value));
    return parsed.toString();
  } catch {
    // Fallback for malformed or relative URLs
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`;
  }
}
