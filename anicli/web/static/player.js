function playerJS(url, headers = {}) {
    const videoContainer = document.getElementById('video-container');
    videoContainer.innerHTML = ''; // Clear previous video

    // Create the video element
    const video = document.createElement('video');
    video.controls = true;
    video.style.width = '100%';
    videoContainer.appendChild(video);

    // Check the video URL to determine the format
    const extension = url.split('.').pop().toLowerCase();

    if (extension === 'mp4') {
        // MP4 video
        video.src = url;
    } else if (extension === 'm3u8') {
        // HLS (M3U8) stream
        if (Hls.isSupported()) {
            const hls = new Hls();
            hls.loadSource(url);
            hls.attachMedia(video);
            hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
        } else {
            video.src = url;
            video.addEventListener('loadedmetadata', () => video.play());
        }
    } else if (extension === 'mpd') {
        // DASH (MPD) stream
        if (dashjs.MediaPlayer.isSupported()) {
            const player = dashjs.MediaPlayer().create();
            player.initialize(video, url, true);
        } else {
            console.error('DASH.js not supported');
        }
    } else {
        console.error('Unsupported video format');
        return;
    }

    // Set custom headers if required
    if (Object.keys(headers).length > 0) {
        const videoSource = video.src;
        const xhr = new XMLHttpRequest();
        xhr.open('GET', videoSource, true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        for (const [key, value] of Object.entries(headers)) {
            xhr.setRequestHeader(key, value);
        }

        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                video.src = URL.createObjectURL(xhr.response);
            } else {
                console.error('Failed to load video with custom headers');
            }
        };

        xhr.responseType = 'blob';
        xhr.send();
    }
}
