from anicli.common.extractors import dynamic_load_extractor_module

from .contexts import AnicliContext
from .ptk_lib import AppContext


async def on_start_config_http_client(ctx: AppContext[AnicliContext]) -> None:
    proxy = ctx.data.get("proxy", None)
    headers = ctx.data.get("headers", {})
    cookies = ctx.data.get("cookies", {})
    timeout = ctx.data.get("timeout", None)

    extractor_instance = dynamic_load_extractor_module(ctx.data["extractor_name"]).Extractor  # type: ignore
    extractor = extractor_instance()
    ctx.data["extractor_instance"] = extractor_instance
    ctx.data["extractor"] = extractor

    # required create new httpx instance for add proxy transport
    if proxy:
        from anicli_api._http import HTTPSync, HTTPAsync  # noqa

        # close old instances and replace a new
        extractor.http.close()
        await extractor.http_async.aclose()

        extractor.http = HTTPSync(proxy=proxy, headers=headers, cookies=cookies, timeout=timeout)
        extractor.http_async = HTTPAsync(proxy=proxy, headers=headers, cookies=cookies, timeout=timeout)
    else:
        extractor.http.headers.update(headers)
        extractor.http.cookies.update(cookies)
        extractor.http.timeout = timeout

        extractor.http_async.headers.update(headers)
        extractor.http_async.cookies.update(cookies)
        extractor.http_async.timeout = timeout
