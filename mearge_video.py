import os
import glob
import tempfile
from pathlib import Path
import ffmpeg
import folder_paths

class VideoMergeNode:
    """
    视频合并节点
    将素材视频和游戏视频按照指定位置关系合并
    支持上下位置合并，自动处理尺寸和时间轴
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
                "material_folder": (cls.get_input_folders(), {"default": "input", "tooltip": "选择素材视频所在的文件夹"}),
                "game_folder": (cls.get_input_folders(), {"default": "input", "tooltip": "选择游戏视频所在的文件夹"}),
                "position": (["up", "down"], {"default": "up", "tooltip": "up: 素材视频在上方, down: 素材视频在下方"}),
                "output_folder_name": ("STRING", {"default": "merged_videos", "multiline": False, "tooltip": "输出文件夹名称，合并后的视频将保存到此文件夹"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_paths",)
    FUNCTION = "merge_videos"
    CATEGORY = "video_editing"
    
    def get_video_info(self, video_path):
        """获取视频信息"""
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if not video_stream:
                return None
                
            return {
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'duration': float(probe['format']['duration']),
                'fps': eval(video_stream['r_frame_rate']),
                'has_audio': audio_stream is not None
            }
        except Exception as e:
            print(f"获取视频信息失败 {video_path}: {str(e)}")
            return None
    
    def resize_video_to_width(self, input_path, target_width, output_path):
        """将视频缩放到指定宽度，保持宽高比"""
        try:
            video_info = self.get_video_info(input_path)
            if not video_info:
                return False
                
            original_width = video_info['width']
            original_height = video_info['height']
            
            # 计算新的高度
            new_height = int((target_width * original_height) / original_width)
            
            # 确保高度是偶数（视频编码要求）
            if new_height % 2 != 0:
                new_height += 1
            
            # 使用ffmpeg进行缩放
            (
                ffmpeg
                .input(input_path)
                .video
                .filter('scale', target_width, new_height)
                .output(output_path, vcodec='libx264', preset='medium')
                .overwrite_output()
                .run(quiet=True)
            )
            
            return True
        except Exception as e:
            print(f"视频缩放失败 {input_path}: {str(e)}")
            return False
    
    def merge_videos_vertically(self, material_path, game_path, output_path, position="up"):
        """垂直合并视频"""
        try:
            # 根据位置确定视频顺序并合并
            if position == "up":
                # 素材在上，游戏在下
                material_input = ffmpeg.input(material_path)
                game_input = ffmpeg.input(game_path)
                
                # 使用vstack filter合并视频
                video_output = ffmpeg.filter([material_input.video, game_input.video], 'vstack', inputs=2)
                
                # 输出合并后的视频，使用游戏的音效
                (
                    ffmpeg
                    .output(
                        video_output,
                        game_input.audio,
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        audio_bitrate='128k',
                        preset='medium'
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
            else:
                # 游戏在上，素材在下
                game_input = ffmpeg.input(game_path)
                material_input = ffmpeg.input(material_path)
                
                # 使用vstack filter合并视频
                video_output = ffmpeg.filter([game_input.video, material_input.video], 'vstack', inputs=2)
                
                # 输出合并后的视频，使用游戏的音效
                (
                    ffmpeg
                    .output(
                        video_output,
                        game_input.audio,
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        audio_bitrate='128k',
                        preset='medium'
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
            
            return True
            
        except Exception as e:
            print(f"视频合并失败: {str(e)}")
            return False
    
    def merge_videos(self, material_folder, game_folder, position, output_folder_name):
        """
        合并视频文件
        
        Args:
            material_folder: 素材文件夹
            game_folder: 游戏视频文件夹
            position: 位置关系（上/下）
            output_folder_name: 输出文件夹名字
        """
        try:
            # 使用ComfyUI的默认输入和输出路径
            base_input_dir = folder_paths.get_input_directory()
            output_folder = folder_paths.get_output_directory()
            
            # 构建完整的输入路径
            if material_folder == "input":
                material_path = base_input_dir
            else:
                material_path = os.path.join(base_input_dir, material_folder)
            
            if game_folder == "input":
                game_path = base_input_dir
            else:
                game_path = os.path.join(base_input_dir, game_folder)
            
            # 验证输入文件夹
            if not os.path.exists(material_path):
                raise ValueError(f"素材文件夹不存在: {material_path}")
            if not os.path.exists(game_path):
                raise ValueError(f"游戏视频文件夹不存在: {game_path}")
            
            # 在输出目录下创建指定名字的文件夹
            output_path = os.path.join(output_folder, output_folder_name)
            os.makedirs(output_path, exist_ok=True)
            
            # 支持的视频格式
            video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm']
            
            # 获取所有游戏视频文件
            game_videos = []
            for ext in video_extensions:
                pattern = os.path.join(game_path, ext)
                game_videos.extend(glob.glob(pattern))
            
            # 获取所有素材视频文件
            material_videos = []
            for ext in video_extensions:
                pattern = os.path.join(material_path, ext)
                material_videos.extend(glob.glob(pattern))
            
            if not game_videos:
                return (f"未找到游戏视频文件",)
            if not material_videos:
                return (f"未找到素材视频文件",)
            
            # 处理每个游戏视频
            processed_count = 0
            material_index = 0
            output_paths = []
            
            for game_video in game_videos:
                if material_index >= len(material_videos):
                    break  # 素材用完则结束
                
                try:
                    # 获取游戏视频信息
                    game_info = self.get_video_info(game_video)
                    if not game_info:
                        continue
                    
                    game_duration = game_info['duration']
                    used_materials = []
                    current_duration = 0
                    
                    # 为当前游戏视频收集足够的素材
                    while current_duration < game_duration and material_index < len(material_videos):
                        material_video = material_videos[material_index]
                        material_info = self.get_video_info(material_video)
                        
                        if not material_info:
                            material_index += 1
                            continue
                        
                        used_materials.append({
                            'path': material_video,
                            'duration': material_info['duration'],
                            'info': material_info
                        })
                        
                        current_duration += material_info['duration']
                        material_index += 1
                    
                    if not used_materials:
                        continue
                    
                    # 生成输出文件名
                    game_filename = Path(game_video).stem
                    output_file = os.path.join(output_path, f"{game_filename}_merged.mp4")
                    
                    # 创建临时合并的素材视频
                    temp_dir = tempfile.mkdtemp()
                    temp_material_path = os.path.join(temp_dir, f"temp_material_{game_filename}.mp4")
                    
                    # 获取游戏视频的宽度
                    game_info = self.get_video_info(game_video)
                    game_width = game_info['width']
                    
                    # 如果只有一个素材且长度足够，直接使用
                    if len(used_materials) == 1 and used_materials[0]['duration'] >= game_duration:
                        # 先将素材宽度对齐到游戏宽度，然后截取到游戏长度
                        (
                            ffmpeg
                            .input(used_materials[0]['path'], t=game_duration)
                            .video
                            .filter('scale', game_width, -1)  # 宽度对齐，高度自动计算
                            .output(temp_material_path, vcodec='libx264', preset='medium')
                            .overwrite_output()
                            .run(quiet=True)
                        )
                    else:
                        # 多个素材需要拼接
                        # 先将每个素材宽度对齐到游戏宽度
                        resized_materials = []
                        for i, material in enumerate(used_materials):
                            resized_path = os.path.join(temp_dir, f"resized_material_{i}.mp4")
                            if self.resize_video_to_width(material['path'], game_width, resized_path):
                                resized_materials.append(resized_path)
                        
                        if not resized_materials:
                            continue
                        
                        # 创建concat文件列表
                        concat_file = os.path.join(temp_dir, f"concat_list_{game_filename}.txt")
                        with open(concat_file, 'w') as f:
                            for resized_material in resized_materials:
                                f.write(f"file '{resized_material}'\n")
                        
                        # 使用concat demuxer拼接视频
                        (
                            ffmpeg
                            .input(concat_file, format='concat', safe=0)
                            .output(temp_material_path, vcodec='libx264', preset='medium')
                            .overwrite_output()
                            .run(quiet=True)
                        )
                        
                        # 清理concat文件和临时缩放文件
                        try:
                            os.remove(concat_file)
                            for resized_material in resized_materials:
                                os.remove(resized_material)
                        except:
                            pass
                        
                        # 截取到游戏长度
                        temp_material_cropped = os.path.join(temp_dir, f"temp_material_cropped_{game_filename}.mp4")
                        (
                            ffmpeg
                            .input(temp_material_path, t=game_duration)
                            .output(temp_material_cropped, vcodec='libx264', preset='medium')
                            .overwrite_output()
                            .run(quiet=True)
                        )
                        
                        # 替换临时文件
                        os.remove(temp_material_path)
                        temp_material_path = temp_material_cropped
                    
                    # 合并素材和游戏视频
                    if self.merge_videos_vertically(temp_material_path, game_video, output_file, position):
                        processed_count += 1
                        output_paths.append(output_file)
                        print(f"成功合并: {game_filename} -> {output_file}")
                    
                    # 清理临时文件和目录
                    try:
                        import shutil
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                    
                except Exception as e:
                    print(f"处理游戏视频 {game_video} 时出错: {str(e)}")
                    continue
            
            if processed_count == 0:
                return (f"未成功处理任何视频",)
            else:
                result_message = f"成功处理 {processed_count} 个游戏视频，保存到: {output_path}\n"
                result_message += f"输出文件:\n" + "\n".join(output_paths)
                return (result_message,)
                
        except Exception as e:
            return (f"处理过程中出错: {str(e)}",)

# 节点映射
NODE_CLASS_MAPPINGS = {
    "VideoMergeNode": VideoMergeNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoMergeNode": "视频合并"
}