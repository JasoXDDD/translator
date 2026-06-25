import unittest

from video_downloader import build_download_command


class VideoDownloaderCommandTests(unittest.TestCase):
    def test_mp4_download_prefers_aac_audio(self):
        """Check that MP4 downloads prefer AAC audio for compatibility."""
        command = build_download_command("yt-dlp", "https://example.com/video", "mp4")

        self.assertIn("--format-sort", command)
        self.assertIn("acodec:aac", command[command.index("--format-sort") + 1])

    def test_webm_download_does_not_apply_mp4_codec_sort(self):
        """Check that WEBM downloads do not get MP4-specific codec sorting."""
        command = build_download_command("yt-dlp", "https://example.com/video", "webm")

        self.assertNotIn("--format-sort", command)

    def test_blank_format_uses_default_yt_dlp_output_mode(self):
        """Check that blank format leaves yt-dlp in its default output mode."""
        command = build_download_command("yt-dlp", "https://example.com/video")

        self.assertNotIn("--merge-output-format", command)
        self.assertNotIn("--remux-video", command)
        self.assertEqual(command[-1], "https://example.com/video")


if __name__ == "__main__":
    unittest.main()
