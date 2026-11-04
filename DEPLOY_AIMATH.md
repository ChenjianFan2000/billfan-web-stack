# aimath.billfan.cn deployment notes

## What is already prepared locally

- Static site home: `/var/www/dist/aimath/index.html`
- Static detail pages: `/var/www/dist/aimath/papers/<slug>/index.html`
- Shared assets: `/var/www/dist/aimath/assets/`
- KaTeX assets: `/var/www/dist/aimath/vendor/katex/`
- Content symlink: `/var/www/dist/content -> /var/www/services/paper-visualizer/paper_visualizer/backend/content`
- Shared root loader: `/var/www/dist/index.html`
- Regeneration script: `/var/www/scripts/build_aimath_static.py`
- Backend router: `/var/www/app/aimath.py`
- Host-aware API dispatch: `/var/www/app/main.py`
- Host refresh script: `/var/www/scripts/deploy/refresh_aimath_host.sh`

## If the domain still jumps to billfan.cn/app

If `aimath.billfan.cn` jumps directly to `https://billfan.cn/app`, the redirect is usually not coming from the static files above.

Most likely causes:

1. Aliyun DNS is using URL forwarding instead of a plain `A` / `CNAME` record.
2. A CDN / ESA / ALB / SLB rule is forcing all subdomains back to `billfan.cn`.
3. The ingress layer has no dedicated `aimath.billfan.cn` host rule yet.

## Aliyun side checklist

1. In the domain console, make sure `aimath.billfan.cn` is a normal `A` or `CNAME` record.
2. Do not use "显性URL转发" / "隐性URL转发" for this subdomain.
3. If you use CDN / ESA / ALB / SLB, add a host rule for `aimath.billfan.cn`.
4. Remove any "redirect to primary domain" rule that matches this host.
5. Ensure HTTPS for `aimath.billfan.cn` is covered by a valid certificate.

## If the page opens but AI Q&A / /api fails

That usually means the host rule is serving `/aimath/` correctly but does not proxy `/api/` to the FastAPI backend yet.

Use the updated template plus refresh script:

```bash
cd /var/www
./scripts/deploy/refresh_aimath_host.sh
```

This script will:

1. Copy `/var/www/deploy/nginx/aimath.billfan.cn.conf.example` to `/etc/nginx/conf.d/aimath.billfan.cn.conf`
2. Verify that `/etc/letsencrypt/live/aimath.billfan.cn/` exists
3. Run `nginx -t`
4. Reload nginx
5. Restart `qh-paper-assistant.service` so new `/var/www/app/aimath.py` code is actually loaded

## Local preview path

Even before the host rule is fixed, the prepared static site should be reachable at:

- `/aimath/`
- `/aimath/papers/<slug>/`
- `/content/<slug>/source.pdf`

as long as the current nginx root is still `/var/www/dist`.
