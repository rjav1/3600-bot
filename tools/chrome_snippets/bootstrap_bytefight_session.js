/*
  bootstrap_bytefight_session.js
  ==============================
  Extracts the current Supabase session + anon key from a logged-in bytefight.org tab
  and downloads `bytefight_session_bootstrap.json` to the user's Downloads folder.

  Usage: run via claude-in-chrome MCP javascript_tool on the bytefight.org tab.

  Then: `python tools/bytefight_client.py bootstrap-auth`

  The anon key is Supabase's public anon key (safe to store — designed to be client-visible).
  The refresh token is sensitive; bytefight_session.json is gitignored.
*/
(async () => {
  // 1. Session from cookie
  const cookieMap = {};
  document.cookie.split(';').forEach(c => {
    const [k, ...rest] = c.trim().split('=');
    if (k) cookieMap[k] = rest.join('=');
  });
  const cookieName = 'sb-pblznfkajrasiprcohrx-auth-token';
  let raw = cookieMap[cookieName];
  if (!raw) return JSON.stringify({err: `no ${cookieName} cookie — are you logged in?`});
  raw = decodeURIComponent(raw);
  if (!raw.startsWith('base64-')) return JSON.stringify({err: 'unexpected cookie format'});
  const session = JSON.parse(atob(raw.slice('base64-'.length)));

  // 2. Anon key — scan all bytefight.org scripts for a JWT adjacent to the supabase ref.
  const allScripts = [...new Set([
    ...Array.from(document.querySelectorAll('script[src]')).map(s => s.src),
    ...performance.getEntriesByType('resource').filter(e => e.name.endsWith('.js')).map(e => e.name),
  ])].filter(s => s.includes('bytefight.org'));
  const jwtRe = /eyJ[A-Za-z0-9_\-]{20,}\.eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}/g;
  const candidates = new Set();
  for (const s of allScripts) {
    try {
      const text = await (await fetch(s)).text();
      if (text.includes('pblznfkajrasiprcohrx')) {
        (text.match(jwtRe) || []).forEach(k => candidates.add(k));
      }
    } catch (_) {}
  }
  let anonKey = null;
  for (const k of candidates) {
    const r = await fetch('https://pblznfkajrasiprcohrx.supabase.co/auth/v1/settings', {
      headers: {apikey: k},
    });
    if (r.ok) { anonKey = k; break; }
  }
  if (!anonKey) return JSON.stringify({err: 'could not find Supabase anon key — try refreshing the page first'});

  const bundle = {
    supabase_url: 'https://pblznfkajrasiprcohrx.supabase.co',
    supabase_project_ref: 'pblznfkajrasiprcohrx',
    supabase_anon_key: anonKey,
    access_token: session.access_token,
    refresh_token: session.refresh_token,
    expires_at: session.expires_at,
    token_type: session.token_type,
    user_id: (session.user || {}).id,
    user_email: (session.user || {}).email,
    team_uuid: '81513423-e93e-4fe5-8a2f-cc0423ccb953',
    _source: 'extracted from bytefight.org cookie via claude-in-chrome',
    _extracted_at: new Date().toISOString(),
  };

  const blob = new Blob([JSON.stringify(bundle, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'bytefight_session_bootstrap.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  return JSON.stringify({
    ok: true,
    downloadedFile: 'bytefight_session_bootstrap.json',
    masked: {
      anon_key: `len=${anonKey.length} starts=${anonKey.slice(0,6)} ends=${anonKey.slice(-4)}`,
      access_token: `len=${bundle.access_token.length} starts=${bundle.access_token.slice(0,6)} ends=${bundle.access_token.slice(-4)}`,
      refresh_token: `len=${bundle.refresh_token.length} starts=${bundle.refresh_token.slice(0,4)} ends=${bundle.refresh_token.slice(-4)}`,
      expires_at_iso: new Date(bundle.expires_at * 1000).toISOString(),
    },
  });
})()
