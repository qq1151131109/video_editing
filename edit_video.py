import os
import cv2
import glob
from pathlib import Path
import ffmpeg
import subprocess
import folder_paths

class VideoCropNode:
    """
    视频裁切节点
    输入文件夹路径，遍历所有视频文件，按指定坐标裁切并保存到目标文件夹
    """
    
    @classmethod
    def get_input_folders(cls):
        """获取输入目录下的所有子文件夹"""
        try:
            input_dir = folder_paths.get_input_directory()
            if not os.path.exists(input_dir):
                return ["input"]
            
            folders = ["input"]  # 默认包含根目录
            for item in os.listdir(input_dir):
                item_path = os.path.join(input_dir, item)
                if os.path.isdir(item_path):
                    folders.append(item)
            
            return sorted(folders)
        except Exception:
            return ["input"]
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_folder": (cls.get_input_folders(), {"default": "input"}),
                "output_folder_name": ("STRING", {"default": "cropped_videos", "multiline": False}),
                "crop_x1": ("INT", {"default": 0, "min": 0, "max": 4096}),
                "crop_y1": ("INT", {"default": 0, "min": 0, "max": 4096}),
                "crop_x2": ("INT", {"default": 1920, "min": 0, "max": 4096}),
                "crop_y2": ("INT", {"default": 1080, "min": 0, "max": 4096}),
            },
            "optional": {
                "keep_audio": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "crop_videos"
    CATEGORY = "video_editing"
    
    def crop_videos(self, input_folder, output_folder_name, crop_x1, crop_y1, crop_x2, crop_y2, keep_audio=True):
        """
        裁切视频文件
        
        Args:
            input_folder: 选择的输入子文件夹
            output_folder_name: 输出文件夹名字
            crop_x1, crop_y1: 左上角坐标
            crop_x2, crop_y2: 右下角坐标
            keep_audio: 是否保留音效
        """
        try:
            # 使用ComfyUI的默认输入和输出路径
            base_input_dir = folder_paths.get_input_directory()
            output_folder = folder_paths.get_output_directory()
            
            # 构建完整的输入路径
            if input_folder == "input":
                # 选择根目录
                input_folder_path = base_input_dir
            else:
                # 选择子文件夹
                input_folder_path = os.path.join(base_input_dir, input_folder)
            
            # 验证输入文件夹
            if not os.path.exists(input_folder_path):
                raise ValueError(f"选择的输入文件夹不存在: {input_folder_path}")
            
            # 在输出目录下创建指定名字的文件夹
            output_path = os.path.join(output_folder, output_folder_name)
            os.makedirs(output_path, exist_ok=True)
            
            # 支持的视频格式
            video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm']
            
            # 遍历所有视频文件
            processed_count = 0
            for ext in video_extensions:
                pattern = os.path.join(input_folder_path, ext)
                video_files = glob.glob(pattern)
                
                for video_file in video_files:
                    try:
                        # 获取文件名（不含扩展名）
                        filename = Path(video_file).stem
                        output_file = os.path.join(output_path, f"{filename}_cropped.mp4")
                        
                        # 计算裁切宽度和高度
                        crop_width = crop_x2 - crop_x1
                        crop_height = crop_y2 - crop_y1
                        
                        # 检查原视频是否有音效
                        has_audio = False
                        try:
                            probe = ffmpeg.probe(video_file)
                            audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
                            has_audio = len(audio_streams) > 0
                        except Exception:
                            has_audio = False
                        
                        # 使用ffmpeg进行裁切
                        if keep_audio and has_audio:
                            # 保留音效的裁切 - 使用更明确的音视频流处理
                            input_stream = ffmpeg.input(video_file)
                            video_stream = input_stream.video.filter('crop', crop_width, crop_height, crop_x1, crop_y1)
                            audio_stream = input_stream.audio
                            
                            (
                                ffmpeg
                                .output(video_stream, audio_stream, output_file, 
                                       vcodec='libx264', acodec='aac', 
                                       audio_bitrate='128k', preset='medium')
                                .overwrite_output()
                                .run(quiet=True)
                            )
                        else:
                            # 不保留音效的裁切
                            (
                                ffmpeg
                                .input(video_file)
                                .video
                                .filter('crop', crop_width, crop_height, crop_x1, crop_y1)
                                .output(output_file, vcodec='libx264', an=None)
                                .overwrite_output()
                                .run(quiet=True)
                            )
                        
                        processed_count += 1
                        audio_status = "保留音效" if (keep_audio and has_audio) else "无音效"
                        print(f"已处理: {video_file} -> {output_file} ({audio_status})")
                        
                    except Exception as e:
                        print(f"处理视频文件 {video_file} 时出错: {str(e)}")
                        continue
            
            if processed_count == 0:
                return (f"未找到可处理的视频文件",)
            else:
                return (f"成功处理 {processed_count} 个视频文件，保存到: {output_path}",)
                
        except Exception as e:
            return (f"处理过程中出错: {str(e)}",)

# 节点映射
NODE_CLASS_MAPPINGS = {
    "VideoCropNode": VideoCropNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoCropNode": "视频裁切节点"
}