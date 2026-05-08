from typing import Dict

import requests
from fastapi import APIRouter, HTTPException, Request, Response

router = APIRouter(tags=["proxy"])

TARGETS: Dict[str, str] = {
    "spark": "http://localhost:8080",
    "hdfs": "http://localhost:9870",
}


def _rewrite_html(body: str, proxy_prefix: str) -> str:
    rewritten = (
        body.replace('href="/', f'href="{proxy_prefix}/')
        .replace("href='/", f"href='{proxy_prefix}/")
        .replace('src="/', f'src="{proxy_prefix}/')
        .replace("src='/", f"src='{proxy_prefix}/")
        .replace('action="/', f'action="{proxy_prefix}/')
        .replace("action='/", f"action='{proxy_prefix}/")
        .replace('url("/', f'url("{proxy_prefix}/')
        .replace("url('/", f"url('{proxy_prefix}/")
    )

    runtime_patch = f"""
<script>
(function() {{
  var p = "{proxy_prefix}";
  function rewrite(u) {{
    if (typeof u !== "string") return u;
    if (u.startsWith("/") && !u.startsWith(p + "/")) return p + u;
    return u;
  }}
  var _fetch = window.fetch;
  if (_fetch) {{
    window.fetch = function(input, init) {{
      if (typeof input === "string") return _fetch.call(this, rewrite(input), init);
      if (input && input.url) {{
        try {{
          var req = new Request(rewrite(input.url), input);
          return _fetch.call(this, req, init);
        }} catch (e) {{}}
      }}
      return _fetch.call(this, input, init);
    }};
  }}
  var _open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url) {{
    return _open.apply(this, [method, rewrite(url)].concat([].slice.call(arguments, 2)));
  }};
}})();
</script>
"""
    if "</head>" in rewritten:
        rewritten = rewritten.replace("</head>", runtime_patch + "\n</head>")
    else:
        rewritten = runtime_patch + rewritten
    return rewritten


@router.get("/proxy/{target}/{path:path}")
def proxy_get(target: str, path: str = "", request: Request = None):
    if target not in TARGETS:
        raise HTTPException(status_code=404, detail="未知代理目标")

    upstream = TARGETS[target].rstrip("/")
    target_url = f"{upstream}/{path}" if path else f"{upstream}/"

    try:
        upstream_resp = requests.get(
            target_url,
            params=dict(request.query_params) if request else None,
            timeout=20,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"代理请求失败: {exc}") from exc

    content_type = upstream_resp.headers.get("Content-Type", "")
    headers = {
        "Cache-Control": "no-store",
    }

    if "text/html" in content_type:
        proxy_prefix = f"/api/proxy/{target}"
        html = _rewrite_html(upstream_resp.text, proxy_prefix)
        return Response(content=html, status_code=upstream_resp.status_code, media_type="text/html", headers=headers)

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        media_type=content_type or None,
        headers=headers,
    )
