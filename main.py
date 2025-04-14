from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword, ReloginAttemptExceeded, ChallengeRequired,
    SelectContactPointRecoveryForm, RecaptchaChallengeForm,
    FeedbackRequired, PleaseWaitFewMinutes, LoginRequired
)
import requests
import os
import time
import json
import moviepy.editor as mp
import multiprocessing
import gc
import psutil
import tempfile
import shutil
import os.path

def json_value(data, *args, default=None):
    curr = data
    for key in args:
        if isinstance(curr, dict) and key in curr:
            curr = curr[key]
        else:
            return default
    return curr

def process_video(video_path, output_path):
    temp_dir = None
    try:
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix="insta_repost_")
        temp_output = os.path.join(temp_dir, "temp_processed.mp4")
        
        # Process in temp directory
        clip = mp.VideoFileClip(video_path)
        clip.write_videofile(temp_output, codec="libx264", logger=None)
        clip.reader.close()
        if clip.audio:
            clip.audio.reader.close_proc()
        clip.close()
        del clip
        gc.collect()
        
        # Move to final destination
        shutil.move(temp_output, output_path)
        
    except Exception as e:
        print(f"🎥 Processing Error: {e}")
    finally:
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"Failed to cleanup temp directory: {e}")

class InstaRepostBot:
    def __init__(self, settings_path="session.json", sessionid=None, username=None, password=None):
        self.client = Client()
        self.settings_path = settings_path
        self.sessionid = sessionid
        self.username = username
        self.password = password
        self.client.handle_exception = self.handle_exception
        self.setup_client()

    def handle_exception(self, client, e):
        if isinstance(e, BadPassword):
            client.logger.exception(e)
            if client.relogin_attempt > 0:
                raise ReloginAttemptExceeded(e)
            self.setup_client()
            return True
        elif isinstance(e, LoginRequired):
            print("🔄 Relogging in...")
            if self.username and self.password:
                client.login(self.username, self.password)
                return True
            raise e
        elif isinstance(e, ChallengeRequired):
            api_path = json_value(client.last_json, "challenge", "api_path")
            if (api_path == "/challenge/"):
                self.setup_client()
            else:
                try:
                    client.challenge_resolve(client.last_json)
                except Exception as e:
                    print(f"❌ Challenge failed: {e}")
                    raise e
            return True
        elif isinstance(e, FeedbackRequired):
            message = client.last_json["feedback_message"]
            print(f"⚠️ Instagram Feedback: {message}")
            time.sleep(1)
        elif isinstance(e, PleaseWaitFewMinutes):
            print("⏳ Rate limited, waiting 1 hour...")
            time.sleep(3600)
            return True
        raise e

    def setup_client(self):
        self.client.set_device({
            "app_version": "244.0.0.17.110",
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
            "dpi": "3.0dpi",
            "resolution": "1170x2532",
            "manufacturer": "Apple",
            "device": "iPhone",
            "model": "iPhone 15",
            "cpu": "arm64-v8a"
        })
        if self.username and self.password:
            try:
                print("Attempting login...")
                self.client.login(self.username, self.password)
                with open(self.settings_path, 'w') as f:
                    json.dump(self.client.get_settings(), f)
            except Exception as e:
                print(f"Login failed: {e}")
                if self.sessionid:
                    self.login_with_direct_sessionid(self.sessionid)
        elif self.sessionid:
            self.login_with_direct_sessionid(self.sessionid)
        else:
            self.login_with_extracted_sessionid()

    def login_with_direct_sessionid(self, sessionid):
        try:
            print("Logging in with sessionid...")
            self.client.login_by_sessionid(sessionid)
        except Exception as e:
            raise Exception("Failed to login with sessionid")

    def login_with_extracted_sessionid(self):
        try:
            if not os.path.exists(self.settings_path):
                raise Exception("Missing session file")
            with open(self.settings_path, 'r') as f:
                session_data = json.load(f)
            sessionid = json_value(session_data, "authorization_data", "sessionid") or \
                        json_value(session_data, "cookies", "sessionid")
            if sessionid:
                self.login_with_direct_sessionid(sessionid)
            else:
                raise Exception("No sessionid found")
        except Exception as e:
            raise Exception("Failed to login with extracted sessionid")

    def download_reel(self, video_url, output_path="temp_reel.mp4"):
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return output_path
        except Exception as e:
            print(f"Download error: {e}")
            return None

    def kill_ffmpeg_processes(self):
        """🔥 Murder any zombie ffmpeg processes"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if "ffmpeg" in proc.info['name'].lower():
                    print(f"💀 Killing ffmpeg PID: {proc.pid}")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass   

    def repost_reel(self, video_path, caption="Find your heavenly vibes 💫"):
        temp_dir = None
        upload_path = None
        media = None

        try:
            # Create temp directory for processing
            temp_dir = tempfile.mkdtemp(prefix="insta_repost_")
            processed_path = os.path.join(temp_dir, "processed_" + os.path.basename(video_path))

            print("\n🎬 Processing Video...")
            p = multiprocessing.Process(target=process_video, args=(video_path, processed_path))
            p.start()
            p.join(timeout=60)
            
            if p.is_alive():
                p.terminate()
                p.join()
                raise Exception("Processing timeout")
                
            self.kill_ffmpeg_processes()
            time.sleep(2)
            upload_path = processed_path
                
            print("📤 Uploading to Instagram...")
            try:
                media = self.client.clip_upload(
                    path=upload_path,
                    caption="Find your heavenly vibes 💫",
                    configure_timeout=10,
                )
                print(f"✅ Upload Complete - ID: {media.id}")
                
                # Check if we got rate limit warning but upload succeeded
                if hasattr(media, 'feedback_message') and "limit how often" in media.feedback_message:
                    print("\n⚠️ Rate limit warning received but upload successful")
                    print("⏳ Waiting 30 minutes before next upload...")
                    time.sleep(1800)  # Wait 30 minutes instead of full hour
                
                return media

            except Exception as e:
                error_msg = str(e).lower()
                if "feedback_required" in error_msg:
                    if "limit how often" in error_msg and media and media.id:
                        print("\n⚠️ Upload succeeded with rate limit warning")
                        print("⏳ Waiting 30 minutes before next upload...")
                        time.sleep(1800)  # Wait 30 minutes
                        return media
                    else:
                        print("⚠️ Rate Limited - Waiting 1 hour...")
                        time.sleep(3600)
                else:
                    print(f"❌ Upload Failed: {e}")
                return None

        finally:
            # Cleanup temp directory and all its contents
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    print("🧹 Cleanup complete")
                except Exception as e:
                    print(f"⚠️ Cleanup failed: {e}")

    def cleanup_temp_file(self, file_path, max_retries=3):
        for attempt in range(max_retries):
            try:
                self.kill_ffmpeg_processes()
                gc.collect()
                time.sleep(2)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print("🧹 Cleanup complete")
                    break
            except Exception:
                if attempt == max_retries - 1:
                    print("⚠️ Unable to remove temporary file")

    def process_new_messages(self, limit=1):
        try:
            threads = self.client.direct_threads(limit)
            if not threads:
                return
            thread = threads[0]
            if not thread.messages:
                return
            latest_message = thread.messages[0]
            print(f"📬 New message from {thread.messages[0].user_id}: {latest_message.text}")
            print(f"📬 Message {latest_message.user_id}, {latest_message.thread_id}")
            if not latest_message.user_id == "youruserid":
                print("❌ Not a valid user/message, skipping...")
                return
            if hasattr(latest_message, 'clip') and latest_message.clip:
                video_url = latest_message.clip.video_url
                caption = "Find your heavenly vibes 💫 \n\n"
                if hasattr(latest_message.clip, 'user') and latest_message.clip.user:
                    caption += f"\n\nReposted from @{latest_message.clip.user.username} \n\n #ambientvibes #chills #aurora #chillvibes #peace #liminal #usa #denver #chill #love #art #runs #colorado #music #nature #drawing #feels #northernlights #travel #creative #solon #hiphop #photography #美术 #haunted #alaska #goodvibes #life #イラスト #auroraborealis #instagood #artwork #artsy #artistic #instaart #instadaily #instalike #instamood #instaartist #instapic #insta"
                video_path = self.download_reel(video_url)
                if video_path:
                    result = self.repost_reel(video_path, caption=caption)
                    try:
                        if os.path.exists(video_path):
                            os.remove(video_path)
                    except Exception as e:
                        print(f"Cleanup failed: {e}")
                    print("Reel reposted!" if result else "Repost failed.")
                    self.client.direct_send_seen(int(latest_message.thread_id))
                    self.client.direct_send(text="✅ Reposted successfully!", thread_ids=[int(latest_message.thread_id)])
        except Exception as e:
            print(f"Error processing messages: {e}")

    def run_continuously(self, check_interval=60):
        print("\n🤖 Bot Active - Monitoring Messages")
        try:
            while True:
                self.process_new_messages()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            print("\n👋 Bot Stopped")

if __name__ == "__main__":
    auth_choice = input("Choose login method:\n1. Username + Password\n2. SessionID\n3. Session File\nChoice: ")
    if auth_choice == "1":
        username = input("Enter Instagram username: ")
        password = input("Enter Instagram password: ")
        bot = InstaRepostBot(username=username, password=password)
    elif auth_choice == "2":
        sessionid = input("Enter your sessionid: ")
        bot = InstaRepostBot(sessionid=sessionid)
    else:
        username = input("Enter Instagram username: ")
        password = input("Enter Instagram password: ")
        bot = InstaRepostBot(username=username, password=password)
    bot.run_continuously(check_interval=15)
