import fs from 'node:fs';
import path from 'node:path';

const ROOT_DIR = path.resolve(import.meta.dirname, '..');
const WELL_KNOWN_DIR = path.join(ROOT_DIR, 'public', '.well-known');

function readEnv(...names) {
  for (const name of names) {
    const value = process.env[name];
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
  }
  return '';
}

function writeJsonFile(filePath, data) {
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`);
}

const iosBundleIdentifier =
  readEnv(
    'NEXT_PUBLIC_IOS_BUNDLE_IDENTIFIER',
    'EXPO_PUBLIC_IOS_BUNDLE_IDENTIFIER',
    'IOS_BUNDLE_IDENTIFIER'
  ) || 'com.manavgupta.mira';
const appleTeamId =
  readEnv('APPLE_TEAM_ID', 'NEXT_PUBLIC_APPLE_TEAM_ID', 'IOS_APPLE_TEAM_ID') || 'XU8BLQACGU';
const androidPackageName =
  readEnv(
    'NEXT_PUBLIC_ANDROID_PACKAGE',
    'EXPO_PUBLIC_ANDROID_PACKAGE',
    'ANDROID_PACKAGE'
  ) || 'com.manavgupta.mira';
const androidFingerprints = readEnv(
  'ANDROID_SHA256_CERT_FINGERPRINTS',
  'NEXT_PUBLIC_ANDROID_SHA256_CERT_FINGERPRINTS'
)
  .split(',')
  .map((value) => value.trim())
  .filter(Boolean);

const appleAppSiteAssociation = {
  applinks: {
    apps: [],
    details: [
      {
        appID: `${appleTeamId}.${iosBundleIdentifier}`,
        paths: ['/share/*', '/auth/callback'],
      },
    ],
  },
};

const assetLinks = [
  {
    relation: ['delegate_permission/common.handle_all_urls'],
    target: {
      namespace: 'android_app',
      package_name: androidPackageName,
      sha256_cert_fingerprints:
        androidFingerprints.length > 0
          ? androidFingerprints
          : ['YOUR_SHA256_FINGERPRINT_HERE'],
    },
  },
];

fs.mkdirSync(WELL_KNOWN_DIR, { recursive: true });
writeJsonFile(
  path.join(WELL_KNOWN_DIR, 'apple-app-site-association'),
  appleAppSiteAssociation
);
writeJsonFile(path.join(WELL_KNOWN_DIR, 'assetlinks.json'), assetLinks);

if (androidFingerprints.length === 0) {
  console.warn(
    '[generate-well-known] ANDROID_SHA256_CERT_FINGERPRINTS is not set; assetlinks.json still contains a placeholder fingerprint.'
  );
}

