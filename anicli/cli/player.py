import warnings

from typing import TYPE_CHECKING, Optional
import subprocess

if TYPE_CHECKING:
    from anicli_api.player.base import Video
    from anicli.cli.config import Config


def _run_ffmpeg_pipeline(*,
                         video: "Video",
                         title: Optional[str],
                         config: "Config"):
    # ffmpeg keys
    loglevel_arg = "-loglevel error"
    url_arg = '-i "{}"'
    hls_args = "-c copy -f hls -hls_flags append_list+omit_endlist " \
               "-hls_segment_type mpegts -hls_playlist_type vod pipe:1"
    player_arg = "| {} {} {} -"
    headers_arg = "-headers "

    # build ffmpeg route cmd commands
    headers_cmd = ""
    if video.headers:
        headers_cmd = f'{headers_arg}"'
        for k, v in video.headers.items():
            headers_cmd += f'{k}: {v}\n'
        headers_cmd += '" '
    url_cmd = url_arg.format(video.url)
    title_cmd = config.PLAYER_ARGS["cmd_title"].format(title) if title else ""
    player_cmd = player_arg.format(config.PLAYER, title_cmd, config.PLAYER_ARGS.get("cmd_extra_args", ""))
    full_cmd = f"ffmpeg {loglevel_arg} {headers_cmd} {url_cmd} {hls_args} {player_cmd}"

    subprocess.Popen(full_cmd, shell=True).wait()


def run_video_command(*,
                      video: "Video",
                      title: Optional[str],
                      config: "Config"):
    # build command
    if config.USE_FFMPEG_ROUTE:
        _run_ffmpeg_pipeline(video=video, title=title, config=config)
    else:
        if video.headers and not config.PLAYER_ARGS["cmd_headers_arg"]:
            warnings.warn(f'missing headers argument or player '
                          f'"{config.PLAYER}" not support this feature, abort', stacklevel=3)
            return
        # build player arguments
        cmd_headers = ""
        if video.headers:
            for k, v in video.headers.items():
                cmd_headers += f"{config.PLAYER_ARGS['cmd_headers_arg'].format(k, v)} "
        cmd_title = config.PLAYER_ARGS["cmd_title"].format(title) if title else ""
        cmd_extra_args = config.PLAYER_ARGS.get("cmd_extra_args", "")
        cmd_full = f'{config.PLAYER} {video.url} {cmd_headers} {cmd_title} {cmd_extra_args}'
        subprocess.Popen(cmd_full, shell=True).wait()
