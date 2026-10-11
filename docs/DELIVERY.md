# DELIVERY — world.execute(me);「程序执行世界」v1.0 交付清单

结项日期：2026-10-11（v18 用户确认通过）。

## 本地成品（仅存本地，绝不进仓库）

| 文件 | 说明 | 大小 |
|---|---|---|
| `out/film_1080p_audio.mp4` | 1080p 带声版（本地人工审片用） | 31,955,072 B |
| `out/film_4k_audio.mp4` | 4K 带声版 | 56,867,276 B |
| `out/film_master.mkv` | 无损母版（FFV1，5085 帧，24fps，211.9s） | 4,146,104,768 B |
| `out/audio_mix.wav` | 混音（歌曲 + 双音提示音 @207.873s，峰值约 −10dB） | 37,380,250 B |
| `out/review_stills/` | 14 个审看时间点静帧（16.04/30.5/68.2/110.41/131.21/147.89/159.2/161.88/162.59/177.44/192.3/205.37/207.873/211.9） | 14 张 |

校验报告：`out/final_report.txt`；各批次报告 `out/report_batchb/c/d/e.txt`；
S13 光棘轮曲线 `out/luma_s13_curve.txt`。

## 公开交付（GitHub）

- 仓库：<https://github.com/ryougishiki27340-lang/world-execute-me-universe>
  （代码、素材与文档；歌曲音频、歌词数据、带声成品均未进入仓库）
- Release v1.0（仅静音版）：
  <https://github.com/ryougishiki27340-lang/world-execute-me-universe/releases/tag/v1.0>
  - 资产：`film_4k_silent.mp4`（51,640,017 B，state=uploaded，
    sha256 ff7c9a3b…）

## 长期边界（与结项状态一致）

- 歌曲音频与带声成品仅存本地，绝不进入仓库；公开仓库与 Release 保持静音版。
- 署名链、非官方声明与 AI 生成内容标注（README/NOTICE/CREDITS）永久保留。
- 不主动添加新内容、不主动重建；维护仅限用户点名并按 v17 第 3 节落点表执行，
  任何改动先文档层说明、经确认再动代码，并完整重跑 audit/闪光/亮度/确定性校验。
