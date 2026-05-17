exports.handler = async (event) => {

  const penv = {
    GUMROAD_PRODUCT_ID: "ldZ7RA2LAQWBrxMnK0hO6A==",
    GITHUB_TOKEN: "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",
    GH_REPO: "sankarnarayanansr/ckpt"
  }

  const { key, os, arch } = event.queryStringParameters || {}
  console.log('[1] Params received:', { key, os, arch })

  if (!key || !os || !arch) {
    console.log('[1] FAIL: Missing params')
    return fail('Missing key, os, or arch.')
  }

  // 1. Verify Gumroad license
  let gr
  try {
    console.log('[2] Verifying license key with Gumroad...')
    gr = await fetch('https://api.gumroad.com/v2/licenses/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        product_id: penv.GUMROAD_PRODUCT_ID,
        license_key: key,
      })
    }).then(r => r.json())
    console.log('[2] Gumroad response:', JSON.stringify(gr))
  } catch (e) {
    console.log('[2] FAIL: Gumroad fetch error:', e.message)
    return fail('Could not reach license server. Try again.')
  }

  if (!gr.success) {
    console.log('[2] FAIL: License invalid. Gumroad said:', gr.message)
    return fail('Invalid license key. Purchase at https://deltapro.site')
  }
  console.log('[2] License valid! Purchaser:', gr.purchase?.email)

  // 2. Map os+arch → exact GitHub asset filename
  const assetMap = {
    'darwin-arm64':   'ckpt-darwin-arm64',
    'darwin-x86_64':  'ckpt-linux-x86_64',
    'linux-arm64':    'ckpt-darwin-arm64',
    'linux-x86_64':   'ckpt-linux-x86_64',
    'macos-arm64':    'ckpt-macos-arm64',
    'macos-x86_64':   'ckpt-linux-x86_64',
    'windows-x86_64': 'ckpt-windows-x86_64.exe',
  }

  const mapKey    = `${os}-${arch}`
  const assetName = assetMap[mapKey]
  console.log('[3] Mapping:', mapKey, '→', assetName)

  if (!assetName) {
    console.log('[3] FAIL: No mapping for:', mapKey)
    return fail(`Unsupported platform: ${os}/${arch}. Contact support@deltapro.site`)
  }

  // 3. Get latest release from private GitHub repo
  let release
  try {
    console.log('[4] Fetching latest release from:', penv.GH_REPO)
    release = await fetch(
      `https://api.github.com/repos/${penv.GH_REPO}/releases/latest`,
      {
        headers: {
          Authorization: `Bearer ${penv.GITHUB_TOKEN}`,
          Accept: 'application/vnd.github+json'
        }
      }
    ).then(r => r.json())
    console.log('[4] Release tag:', release.tag_name)
    console.log('[4] Assets:', release.assets?.map(a => a.name))
  } catch (e) {
    console.log('[4] FAIL: GitHub fetch error:', e.message)
    return fail('Could not reach release server. Try again.')
  }

  // 4. Find the matching asset
  const asset = release.assets?.find(a => a.name === assetName)
  if (!asset) {
    console.log('[5] FAIL: Asset not found. Available:', release.assets?.map(a => a.name))
    return fail(`Binary not found for ${os}/${arch}. Contact support@deltapro.site`)
  }
  console.log('[5] Asset found:', asset.name, '| size:', asset.size, 'bytes')

  // 5. Get GitHub's pre-signed redirect URL for the asset.
  //    Fetch with redirect:'manual' so we capture the Location header
  //    instead of following it — that URL is a short-lived (~5 min) AWS S3
  //    pre-signed URL that the client can download directly, bypassing the
  //    6 MB Lambda payload limit entirely.
  let redirectUrl
  try {
    console.log('[6] Resolving pre-signed download URL...')
    const headRes = await fetch(asset.url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${penv.GITHUB_TOKEN}`,
        Accept: 'application/octet-stream'
      },
      redirect: 'manual'   // <-- do NOT follow the redirect
    })

    console.log('[6] GitHub response status:', headRes.status)

    if (headRes.status === 302 || headRes.status === 301) {
      // GitHub returns a 302 to a pre-signed S3 URL — grab it
      redirectUrl = headRes.headers.get('location')
      console.log('[6] Got pre-signed URL (first 80 chars):', redirectUrl?.slice(0, 80))
    } else {
      // Unexpected — log and fall through to error
      const body = await headRes.text()
      console.log('[6] Unexpected status from GitHub:', headRes.status, body.slice(0, 200))
      return fail('Could not resolve download URL. Try again.')
    }
  } catch (e) {
    console.log('[6] FAIL: URL resolution error:', e.message)
    return fail('Failed to resolve download URL. Try again.')
  }

  if (!redirectUrl) {
    console.log('[6] FAIL: No Location header in GitHub response')
    return fail('Could not obtain download URL. Try again.')
  }

  // 6. Return a 302 redirect to the client.
  //    curl -fsSL in the install script follows redirects automatically,
  //    so the client downloads the binary straight from S3 — no Lambda
  //    payload size limit involved.
  console.log('[7] Redirecting client to pre-signed URL...')
  return {
    statusCode: 302,
    headers: {
      'Location': redirectUrl,
      // Tell the client what filename to save as
      'Content-Disposition': 'attachment; filename="deltapro"'
    },
    body: ''
  }
}

const fail = msg => ({
  statusCode: 403,
  headers: { 'Content-Type': 'text/plain' },
  body: msg
})