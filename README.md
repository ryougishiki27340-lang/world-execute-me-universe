# world.execute(me); — universe

对 Mili《world.execute(me);》的原创同人影像：一支完全由确定性代码绘制的
「数字生命」叙事 MV（1080p/24fps，共 16 段）。歌曲里的「我」被诠释为在
老电脑里运行宇宙的那个进程——她为造物主建世界、写公式，在他离开后以
EXECUTION 挽留，最终把自己的爱写成全片唯一最亮的一帧。

## 重要说明

- 本仓库与 Release **只提供静音版视频**；歌曲音频与歌词时间数据不随仓库分发。
- 非官方粉丝作品：与 Mili 及其版权方无任何关联。
- 全部画面由 Pillow 确定性绘制（`film.py`，`frame(t)` 是歌曲时间的纯函数），
  不使用任何 AI 生图。鲸鱼娘素材仅做裁切/缩放/调色/像素化/合成。
- 逐词字幕基于 `data/lyric_timing.json`（自动对齐草稿，需人工审听）。

## 目录

- `film.py` — 渲染主入口（`--stills`、`--video`、`--master`）
- `src/` — 引擎（prng/draw/post）、组件（字幕/公式/角色）、`cues.py` 时间源
- `data/facts.py` — 全部公式、常数、宇宙史阶段、代码片段（逐条注明来源）
- `tools/` — 审计（audit.py）、闪光安全（check_flash.py）、确定性（verify.py）、
  亮度计（luma.py）、混音（mix_audio.py）、各批次交付报告
- `docs/` — PLAN / STORYBOARD / LEARNED / KIT / PROGRESS

## 渲染

```powershell
.venv\Scripts\python.exe film.py --stills "192.3"          # 单帧
.venv\Scripts\python.exe film.py --master out\film_master.mkv   # 无损母版
```

## 校验

```powershell
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'tools'); import audit; audit.check_batch_a()"
# …check_batch_b/c/d/e、check_s14；tools\check_flash.py out\film.mp4；tools\verify.py
```

## 许可与署名

- 鲸鱼娘角色素材：CC BY-NC-SA 4.0，署名链与上游 LICENSE/NOTICE 见
  `assets/char/notices/` 与 `NOTICE.md`。
- 本工程代码与画面：原创，见 `CREDITS.md`。
